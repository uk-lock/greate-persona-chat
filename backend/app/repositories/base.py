"""リポジトリ共通の基底クラス。"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import AuditMixin


class BaseRepository[ModelT: AuditMixin]:
    """全テーブル共通のCRUD定型処理を提供する基底クラス。

    コミット・ロールバックは行わず、変更はflushまでに留める
    （backend-python.md 14節）。
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        """論理削除されていないレコードをidで取得する。

        Args:
            entity_id: 取得対象のid。

        Returns:
            該当レコード。存在しない、または論理削除済みの場合はNone。
        """
        stmt = select(self.model).where(
            self.model.id == entity_id, self.model.is_deleted.is_(False)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, entity: ModelT) -> ModelT:
        """新規レコードをセッションに登録し、flushする。

        Args:
            entity: 追加対象のエンティティ。

        Returns:
            flush後（idが採番された状態の）エンティティ。
        """
        self._session.add(entity)
        await self.flush()
        return entity

    async def add_all(self, entities: Sequence[ModelT]) -> Sequence[ModelT]:
        """複数の新規レコードをまとめてセッションに登録し、flushする。

        Args:
            entities: 追加対象のエンティティ一覧。

        Returns:
            flush後（idが採番された状態の）エンティティ一覧。
        """
        self._session.add_all(entities)
        await self.flush()
        return entities

    async def flush(self) -> None:
        """セッションに保留中の変更をDBへ反映する（確定のみ、commitはしない）。

        属性の変更自体はサービス層がエンティティに対して直接行うため、
        本メソッドはentityを引数に取らず、その変更を確定するためだけに呼ぶ。
        """
        await self._session.flush()

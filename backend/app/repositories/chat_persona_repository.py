"""チャットとペルソナの中間テーブル（t_chat_persona）のリポジトリ。"""

from app.models.chat_persona import ChatPersona
from app.repositories.base import BaseRepository


class ChatPersonaRepository(BaseRepository[ChatPersona]):
    """t_chat_personaに対するCRUD操作を提供する。

    チャット作成時の複数ペルソナ一括登録は、基底クラスのadd_all（汎用処理）で足りるため
    固有メソッドは現時点では持たない。
    """

    model = ChatPersona

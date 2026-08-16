"use client";

type Props = {
  reset: () => void;
};

/** S03 チャット画面のエラー表示（S03-chat.md 8節・frontend-typescript-react.md 論点10）。 */
const ChatError = ({ reset }: Props) => {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 px-8 py-10">
      <p role="alert" className="text-danger-text">
        チャットの取得に失敗しました。時間をおいて再度お試しください。
      </p>
      <button
        type="button"
        onClick={reset}
        className="rounded-sm border border-gold px-4 py-2 text-sm text-gold hover:bg-wine/40"
      >
        再読み込み
      </button>
    </div>
  );
};

export default ChatError;

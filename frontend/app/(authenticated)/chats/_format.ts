/** `updated_at`のISO日時文字列を、一覧表示用の日時文字列に整形する（S02-chat-history.md 4節）。
 *
 * サーバーのOSタイムゾーン設定に依存せず表示を一定にするため、`timeZone`を明示的に指定する
 * （利用者は日本国内を前提とするアプリのため）。
 */
export const formatUpdatedAt = (isoString: string): string => {
  return new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(isoString));
};

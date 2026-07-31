const SUMMARY_MAX_LENGTH = 50;

/** ペルソナ概要を一覧カード表示用に切り詰める（S04-persona-list.md 12節）。
 *
 * 最大50文字を超える分は末尾を省略し「…」を付ける。`summary`が無い場合は空文字を返す。
 */
export const truncateSummary = (summary: string | null): string => {
  if (!summary) {
    return "";
  }
  if (summary.length <= SUMMARY_MAX_LENGTH) {
    return summary;
  }
  return `${summary.slice(0, SUMMARY_MAX_LENGTH)}…`;
};

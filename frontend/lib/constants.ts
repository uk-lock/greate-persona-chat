/** バックエンドが発行するJWTを格納するCookie名。
 *
 * backend/app/config/constants.py の AUTH_COOKIE_NAME と対応する。frontend/backend間で
 * 値を共有する仕組みが無いため、変更時は両方を同時に更新すること。
 */
export const AUTH_COOKIE_NAME = "access_token";

/** チャット作成時に選択可能なペルソナ数の下限・上限。
 *
 * backend/app/config/constants.py の CHAT_PERSONA_MIN_COUNT / CHAT_PERSONA_MAX_COUNT と対応する。
 * frontend/backend間で値を共有する仕組みが無いため、変更時は両方を同時に更新すること
 * （S01-new-chat.md 7節：マジックナンバーではなく設定値として扱う）。
 */
export const CHAT_PERSONA_MIN_COUNT = 1;
export const CHAT_PERSONA_MAX_COUNT = 5;

/** バックエンドが発行するJWTを格納するCookie名。
 *
 * backend/app/config/constants.py の AUTH_COOKIE_NAME と対応する。frontend/backend間で
 * 値を共有する仕組みが無いため、変更時は両方を同時に更新すること。
 */
export const AUTH_COOKIE_NAME = "access_token";

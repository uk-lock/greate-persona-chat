import { z } from "zod";

/** 半角英数字のみを許容する（db.md m_user.login_id参照）。 */
const LOGIN_ID_PATTERN = /^[A-Za-z0-9]+$/;

/** ログインフォームのバリデーションスキーマ（docs/screens/S00-login.md 7節）。
 *
 * キー名はAPI（POST /auth/login）のリクエストボディ（login_id/password）とform inputの
 * name属性にそのまま合わせ、キャメルケースへの変換処理を挟まない。
 */
export const loginSchema = z.object({
  login_id: z
    .string()
    .min(1, "ログインIDを入力してください")
    .max(255, "ログインIDは255文字以内で入力してください")
    .regex(LOGIN_ID_PATTERN, "ログインIDは半角英数字で入力してください"),
  password: z
    .string()
    .min(1, "パスワードを入力してください")
    .max(255, "パスワードは255文字以内で入力してください"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

/** サインアップフォームのバリデーションスキーマ（docs/screens/S06-signup.md 7節）。
 *
 * `password_confirm`はフロントエンド内の一致確認のみに使い、APIへは送信しない。
 */
export const signupSchema = z
  .object({
    login_id: z
      .string()
      .min(1, "ログインIDを入力してください")
      .max(255, "ログインIDは255文字以内で入力してください")
      .regex(LOGIN_ID_PATTERN, "ログインIDは半角英数字で入力してください"),
    password: z
      .string()
      .min(1, "パスワードを入力してください")
      .max(255, "パスワードは255文字以内で入力してください"),
    password_confirm: z
      .string()
      .min(1, "パスワード確認を入力してください")
      .max(255, "パスワード確認は255文字以内で入力してください"),
  })
  .refine((data) => data.password === data.password_confirm, {
    message: "パスワードが一致しません",
    path: ["password_confirm"],
  });

export type SignupFormValues = z.infer<typeof signupSchema>;

import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { config } from "@/lib/config";
import { AUTH_COOKIE_NAME } from "@/lib/constants";
import { SignupForm } from "./_components/signup-form";

/** S06 サインアップ画面（/signup）。
 *
 * `cookies()`を最初に呼ぶことで、このページを常に動的レンダリングにする。
 * `next build`のページデータ収集時（ビルド環境にはランタイム用の`SIGNUP_ENABLED`が
 * 渡っていない）に、動的API呼び出しより前に`redirect()`で処理が終わってしまうと、
 * Next.jsが「常に同じ結果を返す静的ページ」と誤判定し、ビルド時点の（≒無効化されている）
 * `config.signupEnabled`の値で307リダイレクトを静的にプリレンダーしてしまう
 * （実行時に`SIGNUP_ENABLED=true`を渡しても二度と評価し直されず、/signupが恒久的に
 * 到達不能になる。E2E導入時に発覚した不具合）。
 */
const SignupPage = async () => {
  const cookieStore = await cookies();
  if (cookieStore.has(AUTH_COOKIE_NAME)) {
    redirect("/chats");
  }

  if (!config.signupEnabled) {
    redirect("/login");
  }

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm rounded-md border border-surface-border bg-surface p-8 shadow-xl shadow-black/10">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <h1 className="font-display text-3xl font-bold tracking-widest text-heading">
            偉人チャット
          </h1>
          <span className="h-0.5 w-10 bg-gold" aria-hidden="true" />
          <p className="text-sm text-muted">新しいアカウントを作成する。</p>
        </div>

        <SignupForm />

        <p className="mt-6 text-center text-sm text-muted">
          既にアカウントをお持ちの方は{" "}
          <Link href="/login" className="text-gold underline underline-offset-4">
            ログイン
          </Link>
        </p>
      </div>
    </main>
  );
};

export default SignupPage;

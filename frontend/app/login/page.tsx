import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { config } from "@/lib/config";
import { AUTH_COOKIE_NAME } from "@/lib/constants";
import { LoginForm } from "./_components/login-form";

/** S00 ログイン画面（/login）。 */
const LoginPage = async () => {
  const cookieStore = await cookies();
  if (cookieStore.has(AUTH_COOKIE_NAME)) {
    redirect("/chats");
  }

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm rounded-md border border-surface-border bg-surface p-8 shadow-xl shadow-black/10">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <h1 className="font-display text-3xl font-bold tracking-widest text-heading">
            偉人チャット
          </h1>
          <span className="h-0.5 w-10 bg-gold" aria-hidden="true" />
          <p className="text-sm text-muted">歴史に名を残す偉人と、言葉を交わす。</p>
        </div>

        <LoginForm />

        {config.signupEnabled && (
          <p className="mt-6 text-center text-sm text-muted">
            アカウントをお持ちでない方は{" "}
            <Link href="/signup" className="text-gold underline underline-offset-4">
              サインアップ
            </Link>
          </p>
        )}
      </div>
    </main>
  );
};

export default LoginPage;

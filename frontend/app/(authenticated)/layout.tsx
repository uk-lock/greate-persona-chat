import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AUTH_COOKIE_NAME } from "@/lib/constants";
import { Sidebar } from "./_components/sidebar";

/** S01〜S05共通の認証済みレイアウト。未ログイン時はS00（/login）へリダイレクトする（screen-list.md 3節）。 */
const AuthenticatedLayout = async ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {
  const cookieStore = await cookies();
  if (!cookieStore.has(AUTH_COOKIE_NAME)) {
    redirect("/login");
  }

  return (
    <div className="flex flex-1">
      <Sidebar />
      <main className="flex flex-1 flex-col">{children}</main>
    </div>
  );
};

export default AuthenticatedLayout;

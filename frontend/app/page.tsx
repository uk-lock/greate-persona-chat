import { redirect } from "next/navigation";

/** 画面一覧に対応するルート専用画面が無いため、`/login`へ常時リダイレクトする。 */
const RootPage = () => {
  redirect("/login");
};

export default RootPage;

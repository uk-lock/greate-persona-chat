import Link from "next/link";
import { logoutAction } from "../_actions";

const NewChatIcon = () => {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <path
        d="M4 5h16v10H9l-4 4v-4H4Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M12 8v4M10 10h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
};

const ChatHistoryIcon = () => {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
      <path d="M12 7v5l3.5 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
};

const PersonasIcon = () => {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <circle cx="9" cy="8" r="3" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M15 6.5c1.7.4 3 2 3 3.9 0 1.9-1.3 3.5-3 3.9M18 14c2.3.6 4 2.7 4 5.2"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
};

const LogoutIcon = () => {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <path
        d="M9 4H5v16h4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M13 8l4 4-4 4M17 12H9"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

type NavItem = {
  href: string;
  label: string;
  Icon: () => React.JSX.Element;
};

const navItems: NavItem[] = [
  { href: "/chats/new", label: "新規チャット", Icon: NewChatIcon },
  { href: "/chats", label: "チャット履歴", Icon: ChatHistoryIcon },
  { href: "/personas", label: "ペルソナ一覧", Icon: PersonasIcon },
];

const navLinkClassName =
  "flex h-11 shrink-0 items-center gap-3 rounded-sm px-3 text-muted transition-colors hover:bg-surface hover:text-gold";

const navIconClassName = "flex h-5 w-5 shrink-0 items-center justify-center";

const navLabelClassName =
  "whitespace-nowrap text-sm opacity-0 transition-opacity duration-100 group-hover:opacity-100 group-hover:duration-200 group-hover:delay-100";

/** S01〜S05共通のサイドバー（screen-list.md 3節）。
 *
 * 通常時はアイコン幅のみで表示する。実体は絶対配置のオーバーレイにしてあり、
 * マウスが乗ったときだけ幅とラベルが広がる。外側の枠は常に64px幅を確保する
 * ため、展開してもmain側のレイアウト幅は変化しない。
 */
export const Sidebar = () => {
  return (
    <div className="group relative w-16 shrink-0">
      <nav className="absolute inset-y-0 left-0 z-20 flex w-16 flex-col gap-2 overflow-hidden border-r border-surface-border bg-background py-6 transition-[width] duration-200 ease-out group-hover:w-52 group-hover:shadow-xl group-hover:shadow-black/10">
        {navItems.map(({ href, label, Icon }) => (
          <Link key={href} href={href} title={label} aria-label={label} className={navLinkClassName}>
            <span className={navIconClassName}>
              <Icon />
            </span>
            <span className={navLabelClassName}>{label}</span>
          </Link>
        ))}

        <form action={logoutAction} className="mt-auto">
          <button
            type="submit"
            title="ログアウト"
            aria-label="ログアウト"
            className={`${navLinkClassName} w-full`}
          >
            <span className={navIconClassName}>
              <LogoutIcon />
            </span>
            <span className={navLabelClassName}>ログアウト</span>
          </button>
        </form>
      </nav>
    </div>
  );
};

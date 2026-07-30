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
  "flex h-11 w-11 items-center justify-center rounded-sm text-muted transition-colors hover:bg-surface hover:text-gold";

/** S01〜S05共通のサイドバー（screen-list.md 3節）。
 *
 * 通常時はアイコンのみ表示し、`title`属性によりhover時にラベルを表示する。
 */
export const Sidebar = () => {
  return (
    <nav className="flex w-16 flex-col items-center gap-2 border-r border-surface-border bg-surface/60 py-6">
      {navItems.map(({ href, label, Icon }) => (
        <Link key={href} href={href} title={label} aria-label={label} className={navLinkClassName}>
          <Icon />
        </Link>
      ))}

      <form action={logoutAction} className="mt-auto">
        <button type="submit" title="ログアウト" aria-label="ログアウト" className={navLinkClassName}>
          <LogoutIcon />
        </button>
      </form>
    </nav>
  );
};

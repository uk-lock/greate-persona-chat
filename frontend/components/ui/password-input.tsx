"use client";

import { useId, useState, type InputHTMLAttributes } from "react";

type Props = {
  label: string;
} & Omit<InputHTMLAttributes<HTMLInputElement>, "type">;

/** 目のアイコンで平文表示を切り替えられるパスワード入力欄（S00-login.md・S06-signup.md 共通仕様）。 */
export const PasswordInput = ({ label, id, className, ...inputProps }: Props) => {
  const [visible, setVisible] = useState(false);
  const generatedId = useId();
  const inputId = id ?? generatedId;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="font-display text-sm tracking-wide text-gold">
        {label}
      </label>
      <div className="relative">
        <input
          id={inputId}
          type={visible ? "text" : "password"}
          className={
            className ??
            "w-full rounded-sm border border-surface-border bg-surface px-3 py-2 pr-11 text-foreground placeholder:text-muted focus:border-gold focus:outline-none disabled:opacity-50"
          }
          {...inputProps}
        />
        <button
          type="button"
          aria-label={visible ? "パスワードを非表示にする" : "パスワードを表示する"}
          onClick={() => setVisible((prev) => !prev)}
          className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-muted hover:text-gold"
        >
          {visible ? <EyeOffIcon /> : <EyeIcon />}
        </button>
      </div>
    </div>
  );
};

const EyeIcon = () => {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <path
        d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
};

const EyeOffIcon = () => {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
      <path
        d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
      <path d="M3 3l18 18" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
};

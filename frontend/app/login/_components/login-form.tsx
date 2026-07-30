"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { PasswordInput } from "@/components/ui/password-input";
import { loginSchema, type LoginFormValues } from "@/lib/schemas/auth";
import { loginAction } from "../_actions";

const inputClassName =
  "w-full rounded-sm border border-surface-border bg-surface px-3 py-2 text-foreground placeholder:text-muted focus:border-gold focus:outline-none disabled:opacity-50";

/** S00 ログイン画面のフォーム本体（Client Component）。 */
export const LoginForm = () => {
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    resetField,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    const result = await loginAction(values);
    if (result?.formError) {
      setFormError(result.formError);
      resetField("password");
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex w-full flex-col gap-5">
      {formError && (
        <p
          role="alert"
          className="rounded-sm border border-danger-border bg-danger-bg px-4 py-3 text-sm text-danger-text"
        >
          {formError}
        </p>
      )}

      <div className="flex flex-col gap-1.5">
        <label htmlFor="login_id" className="font-display text-sm tracking-wide text-gold">
          ログインID
        </label>
        <input
          id="login_id"
          type="text"
          autoComplete="username"
          disabled={isSubmitting}
          className={inputClassName}
          {...register("login_id")}
        />
        {errors.login_id && (
          <p className="text-sm text-danger-text">{errors.login_id.message}</p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <PasswordInput
          label="パスワード"
          autoComplete="current-password"
          disabled={isSubmitting}
          {...register("password")}
        />
        {errors.password && (
          <p className="text-sm text-danger-text">{errors.password.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-2 rounded-sm border border-gold bg-wine py-2.5 font-display tracking-widest text-foreground transition-colors hover:bg-wine-bright disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "ログイン中…" : "ログイン"}
      </button>
    </form>
  );
};

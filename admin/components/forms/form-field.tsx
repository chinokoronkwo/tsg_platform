"use client";

import { forwardRef } from "react";

interface FormFieldProps {
  label: string;
  name: string;
  type?: "text" | "email" | "password" | "number" | "url";
  placeholder?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  as?: "input" | "textarea" | "select";
  options?: { value: string; label: string }[];
  rows?: number;
  className?: string;
}

export const FormField = forwardRef<
  HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
  FormFieldProps
>(function FormField(
  {
    label,
    name,
    type = "text",
    placeholder,
    error,
    required,
    disabled,
    value,
    onChange,
    as = "input",
    options,
    rows = 3,
    className = "",
  },
  ref
) {
  const baseInputClasses =
    "w-full px-4 py-2.5 bg-surface-2 border border-cream/10 rounded-lg text-cream placeholder-cream/40 focus:outline-none focus:ring-2 focus:ring-secondary/50 focus:border-secondary/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed";

  return (
    <div className={className}>
      <label
        htmlFor={name}
        className="block text-sm font-medium text-cream/80 mb-2"
      >
        {label}
        {required && <span className="text-secondary ml-1">*</span>}
      </label>
      {as === "textarea" ? (
        <textarea
          ref={ref as React.Ref<HTMLTextAreaElement>}
          id={name}
          name={name}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          rows={rows}
          className={baseInputClasses}
        />
      ) : as === "select" ? (
        <select
          ref={ref as React.Ref<HTMLSelectElement>}
          id={name}
          name={name}
          value={value}
          onChange={onChange}
          disabled={disabled}
          className={baseInputClasses}
        >
          <option value="">Select...</option>
          {options?.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          ref={ref as React.Ref<HTMLInputElement>}
          id={name}
          name={name}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          className={baseInputClasses}
        />
      )}
      {error && (
        <p className="mt-1.5 text-sm text-red-400">{error}</p>
      )}
    </div>
  );
});

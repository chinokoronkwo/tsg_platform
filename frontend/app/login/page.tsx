"use client";

import { useState } from "react";
import Link from "next/link";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement authentication
  };

  return (
    <main className="min-h-screen pt-20 lg:pt-24 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <h1 className="font-heading text-3xl lg:text-4xl text-white text-center mb-2">
          Welcome Back
        </h1>
        <p className="text-cream/80 text-center mb-10">
          Sign in to access your Snob Group account
        </p>

        <form
          onSubmit={handleSubmit}
          className="space-y-6 bg-surface border border-secondary/30 p-8"
        >
          <div>
            <label
              htmlFor="email"
              className="block text-cream/90 text-sm font-medium mb-2"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 bg-primary border border-secondary/30 text-cream placeholder-cream/50 focus:outline-none focus:border-secondary transition-colors"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label
                htmlFor="password"
                className="block text-cream/90 text-sm font-medium"
              >
                Password
              </label>
              <Link
                href="/forgot-password"
                className="text-secondary text-sm hover:text-secondary/90 transition-colors"
              >
                Forgot password?
              </Link>
            </div>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-3 bg-primary border border-secondary/30 text-cream placeholder-cream/50 focus:outline-none focus:border-secondary transition-colors"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-secondary text-white text-sm font-bold uppercase tracking-wider hover:bg-secondary/90 transition-colors"
          >
            Sign In
          </button>
        </form>

        {/* Social login */}
        <div className="mt-8">
          <p className="text-cream/80 text-sm text-center mb-4">
            Or continue with
          </p>
          <div className="flex flex-col gap-3">
            <button
              type="button"
              className="w-full py-3 border border-secondary/30 text-cream text-sm font-medium hover:border-secondary hover:bg-secondary/10 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Google
            </button>
            <button
              type="button"
              className="w-full py-3 border border-secondary/30 text-cream text-sm font-medium hover:border-secondary hover:bg-secondary/10 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13 1.27.5 2.18.48 3.5 0 1.39-.52 1.9-1.07 3.5-.5 1.12-.46 2.27-.4 3.5-.02.12-.02.24-.02.36zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
              </svg>
              Apple
            </button>
            <button
              type="button"
              className="w-full py-3 border border-secondary/30 text-cream text-sm font-medium hover:border-secondary hover:bg-secondary/10 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zm12.6 0H12.6V0H24v11.4z" />
              </svg>
              Microsoft
            </button>
          </div>
        </div>

        <p className="mt-8 text-cream/80 text-sm text-center">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="text-secondary hover:text-secondary/90 transition-colors font-medium"
          >
            Register
          </Link>
        </p>
      </div>
    </main>
  );
}

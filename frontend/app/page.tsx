import { redirect } from "next/navigation";

/**
 * Root page — redirects to the login page.
 * The authenticated app shell will be added in Phase 2.
 */
export default function RootPage() {
  redirect("/login");
}

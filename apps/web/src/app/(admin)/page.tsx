/**
 * Admin Home Page (Story 9.13)
 *
 * Landing page for admin panel, redirects to assignments page.
 */
import { redirect } from 'next/navigation'

export default function AdminPage() {
  redirect('/admin/assignments')
}

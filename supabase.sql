-- ============================================================
-- SUPABASE SETUP (jalankan sekali di: Supabase Dashboard > SQL Editor)
-- ============================================================

create table if not exists public.comments (
  id bigint generated always as identity primary key,
  name text not null,
  message text not null,
  emotion text not null default '💐',
  created_at text not null
);

create table if not exists public.visitors (
  id bigint generated always as identity primary key,
  name text not null,
  visited_at text not null,
  ip_address text,
  user_agent text
);

-- Izinkan akses dari aplikasi Flask (anon key) supaya bisa insert/select/delete
alter table public.comments enable row level security;
alter table public.visitors enable row level security;

create policy "comments_select" on public.comments for select to anon using (true);
create policy "comments_insert" on public.comments for insert to anon with check (true);
create policy "comments_delete" on public.comments for delete to anon using (true);

create policy "visitors_select" on public.visitors for select to anon using (true);
create policy "visitors_insert" on public.visitors for insert to anon with check (true);
create policy "visitors_delete" on public.visitors for delete to anon using (true);
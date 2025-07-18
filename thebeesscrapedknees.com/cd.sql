-- Make sure the uuid-ossp extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-------------------------------------------------------------------------------------------
-- Profiles (Stores user profile data.)
-------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS public.profiles CASCADE;
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID NOT NULL UNIQUE,
    nickname TEXT NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES auth.users (id) ON DELETE CASCADE
);
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own profiles." ON public.profiles 
AS PERMISSIVE FOR ALL
TO authenticated 
USING ( (SELECT auth.uid()) = user_id ) 
WITH CHECK ( (SELECT auth.uid()) = user_id );

-------------------------------------------------------------------------------------------
-- Pages (Stores pages between users and agents.)
-------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS public.pages CASCADE;
CREATE TABLE public.pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID NOT NULL,
    url TEXT NOT NULL,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES auth.users (id) ON DELETE CASCADE
);
ALTER TABLE public.pages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own pages." ON public.pages      
AS PERMISSIVE FOR ALL
TO authenticated
USING ( (SELECT auth.uid()) = user_id )
WITH CHECK ( (SELECT auth.uid()) = user_id );

-------------------------------------------------------------------------------------------
-- Page HTML Data
-------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS public.html CASCADE;
CREATE TABLE public.html (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id UUID NOT NULL,
    meta JSONB NOT NULL,
    html TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID NOT NULL,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES auth.users (id) ON DELETE CASCADE,
    CONSTRAINT fk_page_id FOREIGN KEY (page_id) REFERENCES public.pages (id) ON DELETE CASCADE
);
ALTER TABLE public.html ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own html." ON public.html      
AS PERMISSIVE FOR ALL
TO authenticated
USING ( (SELECT auth.uid()) = user_id )
WITH CHECK ( (SELECT auth.uid()) = user_id );

-------------------------------------------------------------------------------------------
-- Page ETL Data (Stores ETL definitions for different AI pages.)
-------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS public.etl CASCADE;
CREATE TABLE public.etl (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    page_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    etl_name TEXT,
    goal TEXT NOT NULL,
    src_code TEXT NOT NULL,
    html_page_run_id UUID NOT NULL,
    output_json_schema JSONB,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES auth.users (id) ON DELETE CASCADE,
    CONSTRAINT fk_page_id FOREIGN KEY (page_id) REFERENCES public.pages (id) ON DELETE CASCADE
);
ALTER TABLE public.etl ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own etl." ON public.etl      
AS PERMISSIVE FOR ALL
TO authenticated
USING ( (SELECT auth.uid()) = user_id )
WITH CHECK ( (SELECT auth.uid()) = user_id );

-------------------------------------------------------------------------------------------
-- ETL Run Data (Stores ETL run definitions for different AI pages.)
-------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS public.etl_run CASCADE;
CREATE TABLE public.etl_run (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    html UUID NOT NULL,
    etl_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    output_json JSONB,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES auth.users (id) ON DELETE CASCADE,
    CONSTRAINT fk_html FOREIGN KEY (html) REFERENCES public.html (id) ON DELETE CASCADE,
    CONSTRAINT fk_etl_id FOREIGN KEY (etl_id) REFERENCES public.etl (id) ON DELETE CASCADE
);
ALTER TABLE public.etl_run ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own etl_run." ON public.etl_run
AS PERMISSIVE FOR ALL
TO authenticated
USING ( (SELECT auth.uid()) = user_id )
WITH CHECK ( (SELECT auth.uid()) = user_id );



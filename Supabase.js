import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY

if (!supabaseUrl || !supabaseKey) {
    console.error('Missing Supabase environment variables: VITE_SUPABASE_URL and VITE_SUPABASE_KEY')
}

const supabase = createClient(supabaseUrl, supabaseKey)

export default supabase

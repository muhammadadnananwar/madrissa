import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Home, Search } from 'lucide-react';
import Seo from '../components/Seo';

export default function NotFound() {
  return (
    <section className="relative flex min-h-[70vh] items-center overflow-hidden bg-surface py-20">
      <Seo title="Page not found" noIndex />
      <img src="/logo.svg" alt="" className="pointer-events-none absolute -end-20 top-1/2 h-[34rem] -translate-y-1/2 opacity-[0.05]" />
      <div className="container-x relative text-center">
        <motion.p initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
          className="font-display text-[8rem] font-bold leading-none text-primary-700 sm:text-[11rem]">
          4<span className="text-gold-400">0</span>4
        </motion.p>
        <h1 className="mt-2 text-3xl font-bold sm:text-4xl">This page could not be found</h1>
        <p className="mx-auto mt-4 max-w-lg text-slate-600">The page you are looking for may have been moved, renamed or is temporarily unavailable.</p>
        <div className="mt-10 flex flex-wrap justify-center gap-3">
          <Link to="/" className="btn-primary"><Home className="h-4 w-4" />Go to homepage</Link>
          <Link to="/search" className="btn-outline"><Search className="h-4 w-4" />Search the site</Link>
          <button type="button" onClick={() => window.history.back()} className="btn-outline"><ArrowLeft className="h-4 w-4 rtl:rotate-180" />Go back</button>
        </div>
      </div>
    </section>
  );
}

import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, File, Search as SearchIcon } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero } from '../components/common';
import { resultHref, TYPE_ICONS } from '../components/SearchModal';
import { AsyncBlock, ErrorState, PageLoader, RichText, Tabs } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import { formatDate, titleCase } from '../utils/format';
import NotFound from './NotFound';

export function SearchPage() {
  const { t } = useSite();
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const q = params.get('q') || '';
  const [input, setInput] = useState(q);
  const [type, setType] = useState('');
  useEffect(() => setInput(q), [q]);
  const { data, loading, error, reload } = useFetch(q.length >= 2 ? '/public/search' : null, { q });
  const results = (data?.results || []).filter((r) => !type || r.type === type);
  const types = [...new Set((data?.results || []).map((r) => r.type))];

  return (
    <>
      <Seo title={q ? `Search: ${q}` : 'Search'} noIndex />
      <PageHero title={t('search')} crumbs={[{ label: t('search') }]}>
        <form className="relative mt-8 max-w-2xl" onSubmit={(e) => { e.preventDefault(); setParams(input.trim() ? { q: input.trim() } : {}); }}>
          <SearchIcon className="pointer-events-none absolute start-5 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input className="input rounded-full py-4 pe-32 ps-14 text-base" value={input} onChange={(e) => setInput(e.target.value)} placeholder={t('searchPlaceholder')} aria-label={t('search')} />
          <button type="submit" className="btn-gold absolute end-2 top-1/2 -translate-y-1/2">{t('search')}</button>
        </form>
      </PageHero>
      <section className="section bg-surface pt-12">
        <div className="container-x max-w-4xl">
          {q.length < 2 ? <p className="text-center text-slate-500">Type at least 2 characters to search.</p> : (
            <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.results?.length}
              emptyProps={{ icon: SearchIcon, title: `No results for “${q}”`, description: 'Try different keywords or browse our programs.' }}>
              <p className="mb-4 text-sm text-slate-500">{data?.total} results for <b>“{q}”</b></p>
              {types.length > 1 && <Tabs className="mb-6" value={type} onChange={setType} tabs={[{ value: '', label: t('all') }, ...types.map((x) => ({ value: x, label: titleCase(x) }))]} />}
              <div className="space-y-3">
                {results.map((r, i) => {
                  const Icon = TYPE_ICONS[r.type] || File;
                  const onClick = () => (r.external ? window.open(resultHref(r), '_blank', 'noopener') : navigate(r.url));
                  return (
                    // eslint-disable-next-line react/no-array-index-key
                    <button key={i} type="button" onClick={onClick} className="card card-hover flex w-full items-start gap-4 p-5 text-start">
                      <span className="rounded-xl bg-primary-50 p-3 text-primary-700"><Icon className="h-5 w-5" /></span>
                      <span className="min-w-0">
                        <span className="badge bg-gold-50 capitalize text-gold-700">{r.type}</span>
                        <span className="mt-1 block font-semibold text-primary-900">{r.title}</span>
                        {r.description && <span className="mt-1 line-clamp-2 block text-sm text-slate-600">{r.description}</span>}
                      </span>
                    </button>
                  );
                })}
              </div>
            </AsyncBlock>
          )}
        </div>
      </section>
    </>
  );
}

/** Editable CMS pages: /pages/:slug (privacy policy, terms, custom pages). */
export function PageView({ slug: slugProp }) {
  const params = useParams();
  const slug = slugProp || params.slug;
  const { data, loading, error, status, reload } = useFetch(`/public/pages/${slug}`);
  if (loading && !data) return <PageLoader className="min-h-[60vh]" />;
  if (status === 404) return <NotFound />;
  if (error) return <ErrorState message={error} onRetry={reload} className="min-h-[60vh]" />;
  return (
    <>
      <Seo title={data.title} description={data.metaDescription || data.summary} />
      <PageHero title={data.title} subtitle={data.summary} crumbs={[{ label: data.title }]} />
      <section className="section bg-white">
        <div className="container-x max-w-3xl">
          <RichText text={data.content} className="text-lg" />
          <p className="mt-10 text-sm text-slate-400">Last updated {formatDate(data.updatedAt)}</p>
          <Link to="/" className="btn-outline mt-6"><ArrowLeft className="h-4 w-4 rtl:rotate-180" />Back to home</Link>
        </div>
      </section>
    </>
  );
}

export function NotFoundPage() {
  return <NotFound />;
}


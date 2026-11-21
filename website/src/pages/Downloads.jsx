import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Download, FileText, Search } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero } from '../components/common';
import { AsyncBlock, Pagination, Tabs } from '../components/ui';
import { useDebounce, useFetch } from '../hooks/useFetch';
import { API_URL } from '../services/api';
import { formatDate, titleCase } from '../utils/format';

const CATEGORIES = ['prospectus', 'notice', 'examination', 'form', 'policy', 'timetable', 'other'];

export function DownloadList({ initialCategory = '' }) {
  const [category, setCategory] = useState(initialCategory);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState('');
  const dq = useDebounce(q);
  const { data, meta, loading, error, reload } = useFetch('/public/documents', { category, page, q: dq, limit: 12 });

  return (
    <div>
      <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <Tabs value={category} onChange={(v) => { setCategory(v); setPage(1); }} tabs={[{ value: '', label: 'All' }, ...CATEGORIES.map((c) => ({ value: c, label: titleCase(c) }))]} />
        <div className="relative lg:w-72">
          <Search className="pointer-events-none absolute start-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input className="input ps-11" placeholder="Search documents" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Search documents" />
        </div>
      </div>
      <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: FileText, title: 'No documents found' }}>
        <div className="grid gap-4 md:grid-cols-2">
          {data?.map((d) => (
            <div key={d._id} className="card flex items-center gap-4 p-5">
              <span className="flex h-14 w-12 shrink-0 items-center justify-center rounded-lg bg-red-50 text-xs font-bold text-red-600">PDF</span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-semibold text-primary-900">{d.title}</p>
                <p className="truncate text-xs text-slate-500">{titleCase(d.category)} · {formatDate(d.createdAt)}{d.description ? ` · ${d.description}` : ''}</p>
              </div>
              <a href={`${API_URL}/public/documents/${d._id}/download`} target="_blank" rel="noopener noreferrer" className="btn-primary btn-sm shrink-0" aria-label={`Download ${d.title}`}>
                <Download className="h-4 w-4" /><span className="hidden sm:inline">Download</span>
              </a>
            </div>
          ))}
        </div>
        <Pagination meta={meta} onChange={setPage} />
      </AsyncBlock>
    </div>
  );
}

export default function Downloads() {
  const [params] = useSearchParams();
  return (
    <>
      <Seo title="Download Center" description="Prospectus, forms, examination notices and official documents of UMS." />
      <PageHero title="Download Center" subtitle="Prospectus, application forms, examination notices, policies and official documents." crumbs={[{ label: 'Download Center' }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x"><DownloadList key={params.get('category') || 'all'} initialCategory={params.get('category') || ''} /></div>
      </section>
    </>
  );
}

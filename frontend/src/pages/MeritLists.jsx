import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowRight, ListOrdered, Printer, Search } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero } from '../components/common';
import { AsyncBlock, Reveal } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { formatDate } from '../utils/format';

export function MeritListIndex() {
  const { data, loading, error, reload } = useFetch('/public/merit-lists');
  return (
    <>
      <Seo title="Merit Lists" description="Published admission merit lists of UMS." />
      <PageHero title="Merit Lists" subtitle="Merit lists are published here once finalised by the admissions committee."
        crumbs={[{ label: 'Admissions', to: '/admissions' }, { label: 'Merit Lists' }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x">
          <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length}
            emptyProps={{ icon: ListOrdered, title: 'No merit lists published yet', description: 'Please check back after the admission deadline.' }}>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {data?.map((m, i) => (
                <Reveal key={m._id} delay={i * 0.05}>
                  <Link to={`/admissions/merit-lists/${m._id}`} className="card card-hover flex h-full flex-col p-7">
                    <span className="badge w-fit bg-gold-50 text-gold-700">Round {m.round}</span>
                    <h3 className="mt-4 font-sans text-lg font-semibold text-primary-900">{m.title}</h3>
                    <p className="mt-1 text-sm text-slate-600">{m.program?.title} · {m.session}</p>
                    <div className="mt-auto flex items-center justify-between pt-6 text-sm text-slate-500">
                      <span>{m.count} candidates · {formatDate(m.publishedAt)}</span>
                      <ArrowRight className="h-4 w-4 text-gold-500 rtl:rotate-180" />
                    </div>
                  </Link>
                </Reveal>
              ))}
            </div>
          </AsyncBlock>
        </div>
      </section>
    </>
  );
}

export function MeritListDetail() {
  const { id } = useParams();
  const { data, loading, error, reload } = useFetch(`/public/merit-lists/${id}`);
  const [q, setQ] = useState('');
  const rows = useMemo(() => (data?.entries || []).filter((e) => !q || e.applicationNumber.toLowerCase().includes(q.toLowerCase()) || e.name.toLowerCase().includes(q.toLowerCase())), [data, q]);

  return (
    <>
      <Seo title={data?.title || 'Merit List'} />
      <PageHero title={data?.title || 'Merit List'} subtitle={data ? `${data.program?.title} · ${data.session} · Published ${formatDate(data.publishedAt)}` : ''}
        crumbs={[{ label: 'Admissions', to: '/admissions' }, { label: 'Merit Lists', to: '/admissions/merit-lists' }, { label: `Round ${data?.round || ''}` }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x">
          <AsyncBlock loading={loading} error={error} onRetry={reload}>
            {data?.notes && <p className="mb-6 rounded-2xl bg-white p-5 text-sm text-slate-600 shadow-soft">{data.notes}</p>}
            <div className="no-print mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="relative w-full sm:max-w-sm">
                <Search className="pointer-events-none absolute start-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input className="input ps-11" placeholder="Find by application number or name" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search merit list" />
              </div>
              <button type="button" onClick={() => window.print()} className="btn-outline"><Printer className="h-4 w-4" />Print</button>
            </div>
            <div className="card overflow-x-auto">
              <table className="w-full min-w-[540px]">
                <thead className="bg-primary-50"><tr><th className="table-th">Merit #</th><th className="table-th">Application No.</th><th className="table-th">Name</th><th className="table-th">Aggregate</th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {rows.map((e) => (
                    <tr key={e.applicationNumber} className="hover:bg-primary-50/40">
                      <td className="table-td font-display text-xl font-bold text-primary-700">{e.rank}</td>
                      <td className="table-td font-mono">{e.applicationNumber}</td>
                      <td className="table-td font-medium text-primary-900">{e.name}</td>
                      <td className="table-td">{e.aggregate != null ? `${Number(e.aggregate).toFixed(2)}%` : '—'}</td>
                    </tr>
                  ))}
                  {!rows.length && <tr><td colSpan={4} className="table-td py-10 text-center text-slate-500">No matching entries</td></tr>}
                </tbody>
              </table>
            </div>
          </AsyncBlock>
        </div>
      </section>
    </>
  );
}

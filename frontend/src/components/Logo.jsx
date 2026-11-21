import { Link } from 'react-router-dom';
import crest from '../assets/logo.svg';
import { useSite } from '../context/SiteContext';

/** Crest + stacked wordmark. "University of" sits above the name, as on the official crest artwork. */
export default function Logo({ light = false, compact = false, to = '/' }) {
  const { settings } = useSite();
  const name = settings?.universityName || 'University of Muhammadia Saifia';
  const match = name.match(/^(University of)\s+(.+)$/i);
  const top = match ? match[1] : settings?.shortName || 'UMS';
  const main = match ? match[2] : name;

  return (
    <Link to={to} className="group flex shrink-0 items-center gap-3" aria-label={`${name} — home`}>
      <img src={crest} alt="" className={`${compact ? 'h-11' : 'h-12 sm:h-14'} w-auto drop-shadow-sm transition-all duration-300 group-hover:scale-105`} />
      <span className="flex flex-col leading-none">
        <span className={`text-[10px] font-semibold uppercase tracking-[0.3em] ${light ? 'text-gold-300' : 'text-gold-600'}`}>{top}</span>
        <span className={`mt-1 font-display text-xl font-bold sm:text-[22px] ${light ? 'text-white' : 'text-primary-900'}`}>{main}</span>
      </span>
    </Link>
  );
}

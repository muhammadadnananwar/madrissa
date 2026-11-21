import { Helmet } from 'react-helmet-async';
import { useSite } from '../context/SiteContext';

/** Per-page SEO tags. Title is suffixed with the university name. */
export default function Seo({ title, description, image, noIndex = false }) {
  const { settings } = useSite();
  const site = settings?.seo?.defaultTitle || 'University of Muhammadia Saifia (UMS)';
  const fullTitle = title ? `${title} | ${settings?.shortName || 'UMS'}` : site;
  const desc = description || settings?.seo?.defaultDescription || 'Official website of the University of Muhammadia Saifia.';
  const url = typeof window !== 'undefined' ? window.location.href : '';
  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      <link rel="canonical" href={url.split('?')[0]} />
      <meta property="og:type" content="website" />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={desc} />
      <meta property="og:url" content={url} />
      {image && <meta property="og:image" content={image} />}
      <meta name="twitter:card" content="summary_large_image" />
      {noIndex && <meta name="robots" content="noindex,nofollow" />}
    </Helmet>
  );
}

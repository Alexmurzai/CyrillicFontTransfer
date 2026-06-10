import { useState } from 'react';
import { ChevronDown, ZoomIn } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';
import FontCard from '../FontCard/FontCard';
import Slider from '../Slider/Slider';
import './FontFeed.css';

const CATEGORIES = [
  { key: 'all' },
  { key: 'serif' },
  { key: 'sans' },
  { key: 'script' },
  { key: 'display' },
  { key: 'mono' },
];

export default function FontFeed({
  matches,
  visibleCount,
  total,
  onShowMore,
  activeCategory,
  onCategoryChange,
}) {
  const { t } = useI18n();
  const [scale, setScale] = useState(1);

  const visibleMatches = matches.slice(0, visibleCount);
  const hasMore = visibleCount < matches.length;

  const filtered = activeCategory === 'all'
    ? visibleMatches
    : visibleMatches.filter(m => m.font_category === activeCategory);

  return (
    <div className="font-feed" id="font-feed">
      {/* Controls */}
      <div className="font-feed__controls">
        <span className="font-feed__title">{t('match_results')}</span>
        
        <span className="font-feed__status">
          <span className="font-feed__status-dot" />
          {t('ml_model_synced')}
        </span>

        <span className="font-feed__count">
          {filtered.length} {t('of')} {total}
        </span>

        {/* Category filters */}
        <div className="font-feed__filters">
          {CATEGORIES.map(cat => (
            <button
              key={cat.key}
              className={[
                'filter-chip',
                `filter-chip--${cat.key}`,
                activeCategory === cat.key && 'filter-chip--active',
              ].filter(Boolean).join(' ')}
              onClick={() => onCategoryChange?.(cat.key)}
            >
              {t('category_' + cat.key)}
            </button>
          ))}
        </div>

        {/* Scale */}
        <div className="font-feed__scale">
          <ZoomIn size={14} strokeWidth={1.5} className="font-feed__scale-label" />
          <div className="font-feed__scale-input">
            <Slider
              label={t('scale')}
              value={scale}
              min={0.5}
              max={2}
              step={0.1}
              onChange={setScale}
              id="scale-slider"
            />
          </div>
        </div>
      </div>

      {/* Cards list */}
      <div className="font-feed__list">
        {filtered.length === 0 && matches.length > 0 && (
          <div className="font-feed__no-results">
            {t('no_fonts_in_category', { category: t('category_' + activeCategory) })}
          </div>
        )}

        {filtered.map((match, i) => (
          <FontCard
            key={`${match.id}-${match.font_name}`}
            match={match}
            rank={i + 1}
            scale={scale}
            style={{ animationDelay: `${i * 60}ms` }}
          />
        ))}
      </div>

      {/* Show More */}
      {hasMore && (
        <button className="font-feed__more" onClick={onShowMore} id="show-more-btn">
          <ChevronDown size={16} strokeWidth={1.5} />
          {t('btn_show_more')} ({visibleCount} / {matches.length})
        </button>
      )}
    </div>
  );
}

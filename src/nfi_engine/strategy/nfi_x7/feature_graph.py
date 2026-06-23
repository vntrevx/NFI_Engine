from __future__ import annotations

from nfi_engine.strategy import StrategyFrame
from nfi_engine.strategy.nfi_x7.feature_graph_models import (
    X7_FEATURE_GRAPH_CACHE_LIMIT,
    X7FeatureGraphCacheKey,
    X7FeatureGraphCacheStats,
    X7FeatureGraphContext,
    X7FeatureGraphResult,
    X7InformativeCursorSignature,
)
from nfi_engine.strategy.nfi_x7.feature_graph_series import (
    X7InformativeFrames,
    build_feature_graph_result,
    cursor_signature,
)


class X7FeatureGraph:
    """Builds native X7 features and keeps a small mutable cursor cache."""

    def __init__(self) -> None:
        self._cache: dict[X7FeatureGraphCacheKey, X7FeatureGraphResult] = {}
        self._hit_count: int = 0
        self._miss_count: int = 0

    @property
    def cache_stats(self) -> X7FeatureGraphCacheStats:
        return X7FeatureGraphCacheStats(
            hit_count=self._hit_count,
            miss_count=self._miss_count,
            entry_count=len(self._cache),
        )

    def build(self, context: X7FeatureGraphContext) -> X7FeatureGraphResult:
        base_frame = context.base_frame.visible()
        informative_frames = _informative_frames(context)
        cache_key = _cache_key(
            context=context,
            base_frame=base_frame,
            informative_frames=informative_frames,
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._hit_count += 1
            return X7FeatureGraphResult(
                frame=cached.frame,
                coverage=cached.coverage,
                cache_hit=True,
            )
        self._miss_count += 1
        result = build_feature_graph_result(
            base_frame=base_frame,
            informative_frames=informative_frames,
        )
        self._remember(cache_key=cache_key, result=result)
        return result

    def _remember(
        self,
        *,
        cache_key: X7FeatureGraphCacheKey,
        result: X7FeatureGraphResult,
    ) -> None:
        if len(self._cache) >= X7_FEATURE_GRAPH_CACHE_LIMIT:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = result


def _informative_frames(context: X7FeatureGraphContext) -> tuple[X7InformativeFrames, ...]:
    return tuple(
        X7InformativeFrames(
            timeframe=timeframe,
            base_frame=context.provider.get_informative_dataframe(
                pair=context.request.pair,
                timeframe=timeframe,
            ),
            btc_frame=context.provider.get_btc_informative_dataframe(
                pair=context.request.pair,
                timeframe=timeframe,
            ),
        )
        for timeframe in context.request.informative_timeframes
    )


def _cache_key(
    *,
    context: X7FeatureGraphContext,
    base_frame: StrategyFrame,
    informative_frames: tuple[X7InformativeFrames, ...],
) -> X7FeatureGraphCacheKey:
    informative_signatures = tuple(
        signature
        for frames in informative_frames
        for signature in (
            X7InformativeCursorSignature(
                source="base",
                timeframe=frames.timeframe,
                frame=cursor_signature(frames.base_frame),
            ),
            X7InformativeCursorSignature(
                source="btc",
                timeframe=frames.timeframe,
                frame=cursor_signature(frames.btc_frame),
            ),
        )
    )
    return X7FeatureGraphCacheKey(
        pair=context.request.pair,
        base_timeframe=context.request.base_timeframe,
        base_frame=cursor_signature(base_frame),
        informative_frames=informative_signatures,
    )

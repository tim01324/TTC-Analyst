# 60-90 Second Interview Talk Track

I built this project as a BI-style reliability story on TTC subway delays, using 2024 to 2025 operational logs. The problem I wanted to answer was not just where delays happen most often, but where they create the most rider pain.

To do that, I created a reproducible pipeline that cleans multi-format source files, standardizes lines and stations, and applies the same shared business rules across reporting and charts. The key analytical choice was a weighted reliability model: incidents during peak commuting windows receive a 1.5x penalty, because a five-minute delay at rush hour is more costly than the same delay late at night.

The main insight is that reliability risk is concentrated by both line and time of day. Line 1 carries the largest burden, and the hourly heatmap makes the peak-hour pattern immediately visible. On top of that, the station reliability ranking helps turn a large raw dataset into a short operational watchlist. That is the business value: instead of just describing delays, the project prioritizes where attention should go first.

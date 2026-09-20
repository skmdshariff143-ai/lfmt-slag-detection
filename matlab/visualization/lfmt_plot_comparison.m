function lfmt_plot_comparison(X_mm, Y_mm, gt_mask, mf_map, pct_map, rpt_map, defect)
% LFMT_PLOT_COMPARISON Multi-panel comparison figure in MATLAB.

figure('Position', [100, 100, 1100, 400], 'Color', 'w');

subplot(1, 4, 1);
imagesc(X_mm(1, :), Y_mm(:, 1), gt_mask);
colormap(gca, 'gray');
axis xy equal tight;
title('Ground Truth Defect');
xlabel('X [mm]'); ylabel('Y [mm]');
hold on;
viscircles([defect.cx*1e3, defect.cy*1e3], defect.diam*1e3/2, 'Color', 'g', 'LineWidth', 1.5);

subplot(1, 4, 2);
imagesc(X_mm(1, :), Y_mm(:, 1), mf_map);
colormap(gca, 'viridis');
axis xy equal tight;
title('Matched Filter (MF)');
xlabel('X [mm]');
hold on;
viscircles([defect.cx*1e3, defect.cy*1e3], defect.diam*1e3/2, 'Color', 'g', 'LineWidth', 1.5);

subplot(1, 4, 3);
imagesc(X_mm(1, :), Y_mm(:, 1), pct_map);
colormap(gca, 'plasma');
axis xy equal tight;
title('PCT (Optimal EOF)');
xlabel('X [mm]');
hold on;
viscircles([defect.cx*1e3, defect.cy*1e3], defect.diam*1e3/2, 'Color', 'g', 'LineWidth', 1.5);

subplot(1, 4, 4);
imagesc(X_mm(1, :), Y_mm(:, 1), rpt_map);
colormap(gca, 'plasma');
axis xy equal tight;
title('RPT (Random Projection)');
xlabel('X [mm]');
hold on;
viscircles([defect.cx*1e3, defect.cy*1e3], defect.diam*1e3/2, 'Color', 'g', 'LineWidth', 1.5);

sgtitle('LFMT Subsurface Slag Inclusion Processing in MATLAB', 'FontSize', 14, 'FontWeight', 'bold');
end

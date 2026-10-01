clc; clear; close all;

% CSV columns: airport/runway, runway length (ft), runway width (ft)
T = readtable('runways.csv');
lengths = T{:,2};  % Use EVERY runway entry

if ~isnumeric(lengths)
    lengths = str2double(string(lengths));
end
lengths = lengths(~isnan(lengths));

mu = mean(lengths);
sigma = std(lengths);

% Bell curve fitted to all runway lengths
x = linspace(min(lengths)-500, max(lengths)+500, 1000);
y = exp(-0.5*((x-mu)/sigma).^2) ./ (sigma*sqrt(2*pi));

figure
plot(x, y, 'k-', 'LineWidth', 2)
hold on
grid on

% Peak (mean)
xline(mu, 'r-', sprintf('Mean: %.0f ft', mu), 'LineWidth', 2);

% One, two, and three standard deviations from the mean
for k = 1:3
    xline(mu-k*sigma, 'b--', ...
        sprintf('-%d SD: %.0f ft', k, mu-k*sigma), ...
        'LineWidth', 1);

    xline(mu+k*sigma, 'b--', ...
        sprintf('+%d SD: %.0f ft', k, mu+k*sigma), ...
        'LineWidth', 1);
end

xlabel('Runway length (ft)')
ylabel('Probability density')
title('Runway lengths with standard deviation markers')
xlim([min(x), max(x)])

fprintf('Runways included: %d\n', numel(lengths));
fprintf('Mean: %.0f ft\n', mu);
fprintf('Standard deviation: %.0f ft\n', sigma);
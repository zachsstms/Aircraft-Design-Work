%% GENERAL AIRCRAFT PARAMETER PLOT
% Aircraft names are in the first row.
% Parameter names are in the first column.
% Feet-and-inches values are converted to decimal feet.

clear;
clc;
close all;

%% USER SETTINGS

csvFile = 'comp_brief.csv';

% Enter parameter names exactly as they appear in the CSV.
xParameter = "W/S (lb/sq.ft)";
yParameter = "Range @ Max Payload (nm)";

% Available sections:
% "General"
% "Constraints"
% "Dimensions (Cabin)"
% "Geometry"
% "Engine"
% "Thrust"

xSection = "General";
ySection = "General";

% Example for geometry:
% xParameter = "Wing Span";
% xSection   = "Geometry";
% yParameter = "Length";
% ySection   = "Geometry";

connectPoints = false;
showAircraftNames = true;

% Leave empty for automatic axis limits.
xLimits = [];
yLimits = [];

% Highlight this aircraft if present in the CSV.
highlightAircraft = "OUR PLANE";

%% READ CSV

data = readcell(csvFile, 'Delimiter', ',');

if size(data, 1) < 2 || size(data, 2) < 2
    error('The CSV must contain aircraft names and parameter data.');
end

aircraftNames = strings(1, size(data, 2) - 1);

for column = 2:size(data, 2)
    aircraftNames(column - 1) = cleanText(data{1, column});
end

parameterNames = strings(size(data, 1) - 1, 1);

for row = 2:size(data, 1)
    parameterNames(row - 1) = cleanText(data{row, 1});
end

aircraftData = data(2:end, 2:end);

%% REMOVE COLUMNS WITHOUT AIRCRAFT NAMES

validAircraftColumns = strlength(aircraftNames) > 0;

aircraftNames = aircraftNames(validAircraftColumns);
aircraftData = aircraftData(:, validAircraftColumns);

%% IDENTIFY SECTIONS AND PARAMETER ROWS

sectionHeaders = [
    "Constraints"
    "Dimensions (Cabin)"
    "Geometry"
    "Engine"
    "Thrust"
];

parameterSections = strings(size(parameterNames));
isParameterRow = false(size(parameterNames));

currentSection = "General";

for row = 1:numel(parameterNames)

    name = parameterNames(row);

    if strlength(name) == 0
        continue;
    end

    if any(strcmpi(name, sectionHeaders))
        currentSection = name;
        continue;
    end

    parameterSections(row) = currentSection;
    isParameterRow(row) = true;

end

%% SHOW AVAILABLE PARAMETERS

fprintf('\nAvailable parameters:\n');

for row = 1:numel(parameterNames)

    if isParameterRow(row)
        fprintf('  [%s] %s\n', ...
            char(parameterSections(row)), ...
            char(parameterNames(row)));
    end

end

%% GET SELECTED PARAMETER DATA

[xData, xIsFeet] = getParameter( ...
    aircraftData, parameterNames, parameterSections, ...
    isParameterRow, xParameter, xSection);

[yData, yIsFeet] = getParameter( ...
    aircraftData, parameterNames, parameterSections, ...
    isParameterRow, yParameter, ySection);

%% REMOVE AIRCRAFT MISSING X OR Y DATA

validPoints = isfinite(xData) & isfinite(yData);

xPlot = xData(validPoints);
yPlot = yData(validPoints);
namesPlot = aircraftNames(validPoints);

if isempty(xPlot)
    error(['No aircraft have valid numeric data for both ' ...
        'selected parameters.']);
end

if any(~validPoints)

    fprintf('\nSkipped aircraft with missing or invalid data:\n');

    skippedNames = aircraftNames(~validPoints);

    for i = 1:numel(skippedNames)
        fprintf('  %s\n', char(skippedNames(i)));
    end

end

%% CREATE PLOT

figure('Color', 'white', 'Position', [100 100 1000 750]);

hold on;
grid on;
box on;

% Sort by X before connecting points.
if connectPoints

    [xPlot, sortOrder] = sort(xPlot);
    yPlot = yPlot(sortOrder);
    namesPlot = namesPlot(sortOrder);

    plot(xPlot, yPlot, '-ok', ...
        'LineWidth', 1.25, ...
        'MarkerSize', 7, ...
        'MarkerFaceColor', 'white');

else

    scatter(xPlot, yPlot, 90, 'k', 'filled');

end

%% HIGHLIGHT OUR AIRCRAFT IF PRESENT

highlightPoint = strcmpi( ...
    strtrim(namesPlot), strtrim(highlightAircraft));

if any(highlightPoint)

    scatter(xPlot(highlightPoint), yPlot(highlightPoint), ...
        140, 'red', 'filled', ...
        'MarkerEdgeColor', 'black');

end

%% LABEL EACH AIRCRAFT

xRange = max(xPlot) - min(xPlot);
yRange = max(yPlot) - min(yPlot);

if xRange == 0
    xRange = max(abs(xPlot(1)), 1);
end

if yRange == 0
    yRange = max(abs(yPlot(1)), 1);
end

if showAircraftNames

    for i = 1:numel(xPlot)

        labelColor = 'black';

        if highlightPoint(i)
            labelColor = 'red';
        end

        text(xPlot(i) + 0.015*xRange, ...
             yPlot(i) + 0.015*yRange, ...
             namesPlot(i), ...
             'FontSize', 10, ...
             'Color', labelColor, ...
             'Interpreter', 'none');

    end

end

%% FORMAT PLOT

xLabel = xParameter;
yLabel = yParameter;

if xIsFeet
    xLabel = xLabel + " (ft)";
end

if yIsFeet
    yLabel = yLabel + " (ft)";
end

xlabel(xLabel, 'Interpreter', 'none');
ylabel(yLabel, 'Interpreter', 'none');


if isempty(xLimits)
    xlim([min(xPlot) - 0.08*xRange, ...
          max(xPlot) + 0.25*xRange]);
else
    xlim(xLimits);
end

if isempty(yLimits)
    ylim([min(yPlot) - 0.08*yRange, ...
          max(yPlot) + 0.12*yRange]);
else
    ylim(yLimits);
end

axis square;
set(gca, 'FontSize', 14);

hold off;

%% MOVE LABELS MANUALLY, THEN SAVE

fig = gcf;

% Enable clicking and dragging labels.
plotedit(fig, 'on');
drawnow;

% Wait while you arrange labels in the figure window.
input('Drag the labels into position, then press Enter here to save: ', 's');

% Turn off editing before exporting.
plotedit(fig, 'off');
drawnow;

% Create a valid filename.
fileName = yLabel + " versus " + xLabel;
fileName = regexprep(fileName, '[<>:"/\\|?*]', '_');

% Save the adjusted plot as a PNG.
exportgraphics(fig, fileName + ".png", 'Resolution', 300);

% Also save an editable MATLAB figure.
savefig(fig, fileName + ".fig");
%% LOCAL FUNCTIONS

function textValue = cleanText(value)

    textValue = "";

    if isempty(value)
        return;
    end

    if ~(ischar(value) || isstring(value) || isnumeric(value))
        return;
    end

    converted = string(value);

    if ~isscalar(converted) || ismissing(converted)
        return;
    end

    textValue = strtrim(converted);

end


function [values, isFeet] = getParameter( ...
    aircraftData, parameterNames, parameterSections, ...
    isParameterRow, selectedParameter, selectedSection)

    matches = isParameterRow & ...
        strcmpi(parameterNames, strtrim(selectedParameter));

    % An empty section is allowed for uniquely named parameters.
    if strlength(strtrim(selectedSection)) > 0
        matches = matches & ...
            strcmpi(parameterSections, strtrim(selectedSection));
    end

    rowNumbers = find(matches);

    if isempty(rowNumbers)

        error('Parameter "%s" was not found in section "%s".', ...
            char(selectedParameter), char(selectedSection));

    elseif numel(rowNumbers) > 1

        error(['Parameter "%s" occurs more than once. ' ...
            'Choose its section using xSection or ySection.'], ...
            char(selectedParameter));

    end

    values = NaN(1, size(aircraftData, 2));
    isFeet = false;

    for column = 1:size(aircraftData, 2)

        [values(column), convertedFeet] = ...
            convertToNumber(aircraftData{rowNumbers, column});

        isFeet = isFeet || convertedFeet;

    end

end


function [number, isFeet] = convertToNumber(value)

    number = NaN;
    isFeet = false;

    if isempty(value)
        return;
    end

    if isnumeric(value)

        if isscalar(value) && isfinite(value)
            number = double(value);
        end

        return;

    end

    textValue = cleanText(value);

    if strlength(textValue) == 0
        return;
    end

    % Skip Excel errors, including #DIV/0! and #REF!.
    if startsWith(textValue, "#")
        return;
    end

    % Remove thousands separators.
    textValue = erase(textValue, ",");
    rawText = char(textValue);

    % Match feet and optional inches:
    % 87'10" -> 87 + 10/12 feet
    % 98'    -> 98 feet
    feetPattern = ...
        '^\s*(\d+(?:\.\d+)?)\s*''\s*(\d+(?:\.\d+)?)?\s*"?\s*$';

    feetTokens = regexp(rawText, feetPattern, 'tokens', 'once');

    if ~isempty(feetTokens)

        feet = str2double(feetTokens{1});
        inches = 0;

        if numel(feetTokens) >= 2 && ~isempty(feetTokens{2})
            inches = str2double(feetTokens{2});
        end

        number = feet + inches/12;
        isFeet = true;
        return;

    end

    % Accept a number with optional trailing unit text,
    % such as 2650 [nm] or 72750 lb.
    numberText = regexp(rawText, ...
        '^\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)', ...
        'tokens', 'once');

    if ~isempty(numberText)
        number = str2double(numberText{1});
    end

end
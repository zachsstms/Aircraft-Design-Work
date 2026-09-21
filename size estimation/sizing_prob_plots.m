%% GENERAL AIRCRAFT PARAMETER PLOT
% Choose any two parameters from comp_plane_sizing.csv.

clear;
clc;
close all;

%% USER SETTINGS

csvFile = 'comp_plane_sizing.csv';

% Enter the row names exactly as they appear in the CSV.
xParameter = "Range";
yParameter = "Max Take-Off Weight [lb]";

connectPoints = false;
showAircraftNames = true;


%% READ CSV

data = readcell(csvFile);

aircraftNames = string(data(1, 2:end));
parameterNames = string(data(2:end, 1));

aircraftData = data(2:end, 2:end);


%% REMOVE COLUMNS WITHOUT AIRCRAFT NAMES

validAircraftColumns = ...
    ~ismissing(aircraftNames) & ...
    strlength(strtrim(aircraftNames)) > 0;

aircraftNames = aircraftNames(validAircraftColumns);
aircraftData = aircraftData(:, validAircraftColumns);


%% SHOW AVAILABLE PARAMETERS

fprintf('\nAvailable parameters:\n');

for i = 1:length(parameterNames)

    if ~ismissing(parameterNames(i))

        fprintf('%s\n', parameterNames(i));

    end

end


%% GET SELECTED PARAMETER DATA

xData = getParameter( ...
    aircraftData, ...
    parameterNames, ...
    xParameter);

yData = getParameter( ...
    aircraftData, ...
    parameterNames, ...
    yParameter);


%% REMOVE AIRCRAFT MISSING X OR Y DATA

validPoints = isfinite(xData) & isfinite(yData);

xPlot = xData(validPoints);
yPlot = yData(validPoints);

namesPlot = aircraftNames(validPoints);


%% CREATE PLOT

figure('Color', 'white');

hold on;
grid on;
box on;

if connectPoints

    plot( ...
        xPlot, ...
        yPlot, ...
        '-ok', ...
        'LineWidth', 1.25, ...
        'MarkerSize', 7, ...
        'MarkerFaceColor', 'white');

else

    scatter( ...
        xPlot, ...
        yPlot, ...
        90, ...
        'k', ...
        'filled');

end

ourPlanePoint = strcmpi(strtrim(namesPlot), "OUR PLANE");

scatter( ...
    xPlot(ourPlanePoint), ...
    yPlot(ourPlanePoint), ...
    140, ...
    'red', ...
    'filled', ...
    'MarkerEdgeColor', 'black');


%% LABEL EACH AIRCRAFT

if showAircraftNames

    xRange = max(xPlot) - min(xPlot);
    yRange = max(yPlot) - min(yPlot);

    if xRange == 0
        xRange = 1;
    end

    if yRange == 0
        yRange = 1;
    end

    for i = 1:length(xPlot)

        text( ...
            xPlot(i) + 0.01*xRange, ...
            yPlot(i) + 0.01*yRange, ...
            namesPlot(i), ...
            'FontSize', 9, ...
            'Interpreter', 'none');

    end

end


%% FORMAT PLOT

xlabel(xParameter, 'Interpreter', 'none');
ylabel(yParameter, 'Interpreter', 'none');

title( ...
    yParameter + " versus " + xParameter, ...
    'Interpreter', 'none');

ylim([1e5, 1.7e5])

axis square

set(gca, 'FontSize', 16);

hold off;


%% LOCAL FUNCTIONS

function values = getParameter( ...
    aircraftData, parameterNames, selectedParameter)

    rowNumber = find( ...
        strcmpi( ...
            strtrim(parameterNames), ...
            strtrim(selectedParameter)), ...
        1);

    if isempty(rowNumber)

        error( ...
            'Parameter "%s" was not found in the CSV.', ...
            selectedParameter);

    end

    values = NaN(1, size(aircraftData, 2));

    for column = 1:size(aircraftData, 2)

        values(column) = ...
            convertToNumber(aircraftData{rowNumber, column});

    end

end


function number = convertToNumber(value)

    if isempty(value)

        number = NaN;
        return;

    end

    try

        if ismissing(value)

            number = NaN;
            return;

        end

    catch
    end

    if isnumeric(value)

        number = double(value);
        return;

    end

    textValue = string(value);

    if ismissing(textValue) || ...
            strlength(strtrim(textValue)) == 0

        number = NaN;
        return;

    end

    % Remove commas from values such as 67,999.
    textValue = erase(textValue, ",");

    % Extract the number from values such as 2650 [nm].
    numberText = regexp( ...
        char(textValue), ...
        '[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', ...
        'match', ...
        'once');

    if isempty(numberText)

        number = NaN;

    else

        number = str2double(numberText);

    end

end
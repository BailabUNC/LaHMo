% Convert the table to an array
data = table2array(adamsapplelocationsACTUAL);

% Extract data from the array
time = data(:, 1); % Assuming time is in the first column
x = data(:, 2);    % Assuming x-position is in the second column
y = data(:, 3);    % Assuming y-position is in the third column

% Define the grid for interpolation
x_interp = linspace(min(x), max(x), 100); % You can adjust the number of points
y_interp = linspace(min(y), max(y), 100); % and the range as needed
[xq, yq] = meshgrid(x_interp, y_interp);

% Interpolate the time data on the grid
time_interp = griddata(x, y, time, xq, yq, 'cubic');

% Create a 2D scatter plot
scatter(x, y, 20, time, 'filled');
colorbar;
colormap('jet');
xlabel('X Position');
ylabel('Y Position');
title('Scatter Plot with Interpolated Time Data');

% Add lines connecting the points
hold on;
plot(x, y, 'k-'); % Connect the points with black lines
hold off;


%% Another attempt

% Convert the table to an array
data = table2array(adamsapplelocationsACTUAL);


function interpolatedData = interpolateXYZ(table)
    % Extract data from the table
    time = table(:, 1); % Assuming time is in column 1
    x = table(:, 2);    % Assuming x-position is in column 2
    y = table(:, 3);    % Assuming y-position is in column 3

    % Create a time grid with higher resolution
    t_interp = linspace(min(time), max(time), 1000);

    % Interpolate x and y values for each time point
    x_interp = interp1(time, x, t_interp, 'spline');
    y_interp = interp1(time, y, t_interp, 'spline');

    % Combine the interpolated x, y, and time values into a table
    interpolatedData = table(t_interp', x_interp', y_interp');
    % Assign meaningful variable names to the table
    interpolatedData.Properties.VariableNames = {'Time', 'X_Position', 'Y_Position'};

    % Display the interpolated data in a table
    disp('Interpolated Data Table:');
    disp(interpolatedData);
end

% Call the interpolateXYZ function to get the interpolated data
interpolatedData = interpolateXYZ(adamsapplelocationsACTUAL);

% Display the interpolated data in a table
disp('Interpolated Data Table:');
disp(interpolatedData);

function interpolatedData = interpolateXYZ(table)
    % Extract data from the table
    time = table(:, 1); % Assuming time is in column 1
    x = table(:, 2);    % Assuming x-position is in column 2
    y = table(:, 3);    % Assuming y-position is in column 3

    % Create a time grid with higher resolution
    t_interp = linspace(min(time), max(time), 1000);

    % Interpolate x and y values for each time point
    x_interp = interp1(time, x, t_interp, 'spline');
    y_interp = interp1(time, y, t_interp, 'spline');

    % Combine the interpolated x, y, and time values into a table
    interpolatedData = table(t_interp', x_interp', y_interp');
    % Assign meaningful variable names to the table
    interpolatedData.Properties.VariableNames = {'Time', 'X_Position', 'Y_Position'};
end



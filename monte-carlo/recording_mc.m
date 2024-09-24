clc
clear
close all
mcx_include();

% Load skin optical properties
if exist('TISSUE_PROPERTIES_MAT', 'var') ~= 1
    load("tissue_properties.mat");
end

%% Normal status

% Initialize the skin geometry
% 0-background, 1-epidermis, 2-dermis, 3-subcutaneous adipose, 4-muscle
% 5-cartilage

% according to the size of the LED, 1 voxel = 0.5 mm (approximately)
% here we use epidermis = 1 mm, dermis = 3 mm
l1 = 3;
l2 = 7;
l3 = 20;
l4 = 70;

box_size = 120;
tissue_size = l1+l2+l3+l4;
offset = (box_size-tissue_size)/2;
voxel_space = flat_space_generate(l1, l2, l3, l4, offset, box_size);

% Define simulation configuration
cfg1.seed = 114514;
cfg1.nphoton = 1e7;
cfg1.debuglevel = 'P';

cfg1.vol = voxel_space;
cfg1.vol(:, :, 1) = 0; % pad a layer of 0s to get diffuse reflectance
cfg1.prop = [0,             0,             1,           1;
             tprop.mua_epi, tprop.mus_epi, tprop.g_epi, tprop.n_epi;
             tprop.mua_der, tprop.mus_der, tprop.g_der, tprop.n_der;
             tprop.mua_adi, tprop.mus_adi, tprop.g_adi, tprop.n_adi;
             tprop.mua_mus, tprop.mus_mus, tprop.g_mus, tprop.n_mus;
             tprop.mus_car, tprop.mus_car, tprop.g_car, tprop.n_car];
cfg1.issrcfrom0 = 1;
cfg1.issaveref = 1;
cfg1.gpuid = 1;
cfg1.autopilot = 1;

cfg1.tstart = 0;
cfg1.step = 1e-12;

cfg1.maxjumpdebug = 1e8;

% Define light source
cfg1.srctype = 'zgaussian';
cfg1.srcparam1(1) = 20;        % variance in the zenith angle
cfg1.srcpos = [box_size/2, box_size/4, offset-1];
cfg1.srcdir = [0, 0, 1];

% Define light detector
cfg1.detpos = [cfg1.srcpos(1), cfg1.srcpos(2)-15, cfg1.srcpos(3)+2, 2];
cfg1.savedetflag = 'dspmxvw';

% Simulation period
cfg1.tend = 2.5e-10;

% Second light src
cfg2 = cfg1;
cfg2.srcpos = [box_size/2, box_size * 3/4, offset-1];

fluence1 = mcxlab(cfg1);
fluence2 = mcxlab(cfg2);
lgcwfluence_example = log(fluence1.data + fluence2.data);

f1 = figure;
f1.Position(1:2) = [1000, 300];
f1.Position(3:4) = [800, 800];

% plot configs and results
ax1 = subplot(221);
mcxpreview(cfg1);
ax1.Title.String = 'domain preview';
axis equal

ax2 = subplot(222);
imagesc(squeeze(lgcwfluence_example(:, 50, :)));
view(270, 90);
ax2.XLim = [0, box_size];
ax2.YLim = [0, box_size];
ax2.CLim = [9, 18];
ax2.DataAspectRatio = [1, 1, 1];
ax2.Title.String = 'fluence at x=60';
colorbar;
hold on
xline(offset+l1, 'w--');
hold on
xline(offset+l1+l2, 'w--');
hold on
xline(offset+l1+l2+l3, 'w--');
hold off

ax3 = subplot(223);
target = max(lgcwfluence_example(:)) - 8;
[xx1, yy1, zz1] = ind2sub(size(lgcwfluence_example), ...
                          find(lgcwfluence_example > target - 0.01 ...
                             & lgcwfluence_example < target + 0.01));
scatter3(xx1, yy1, zz1, 1, "filled", ...
         LineWidth=0.1);
ax3.XLim = [0, box_size];
ax3.YLim = [0, box_size];
ax3.ZLim = [0, box_size];
ax3.BoxStyle = "full";
ax3.DataAspectRatio = [1, 1, 1];
grid off

ax4 = subplot(224);
imagesc(squeeze(lgcwfluence_example(:, :, cfg1.detpos(3))));
ax4.XLim = [0, box_size];
ax4.YLim = [0, box_size];
ax4.CLim = [9, 18];
ax4.DataAspectRatio = [1, 1, 1];
ax4.Title.String = 'fluence at z=6';
colorbar;

figure;
imagesc(squeeze(lgcwfluence_example(60, :, :)));
view(270, 90);

ax = gca;
ax.XLim = [0, box_size];
ax.YLim = [0, box_size];
ax.CLim = [9, 18];
ax.DataAspectRatio = [1, 1, 1];
ax.Title.String = 'fluence at x=60';
colorbar;
hold on
xline(offset+l1, 'w--');
hold on
xline(offset+l1+l2, 'w--');
hold on
xline(offset+l1+l2+l3, 'w--');
hold off

% writematrix(squeeze(lgcwfluence1(50, :, :)), 'maps/flat.txt');

%% Loop through actions
filename = 'recording/actions.txt';
fid = fopen(filename);
data = textscan(fid, '%f %f %f %c');
timestamps = data{1};
centers = data{2};
heights = data{3};
actions = data{4};
fclose(fid);

fid = fopen('recording/src_loc.txt', 'a');

for i = 1: size(timestamps)
    close all;
    
    cfg3 = cfg1;
    % cfg3.tend = 5e-10;
    
    % Voxel space
    bump_center = [centers(i), 60];
    bump_height = heights(i);
    bump_width = 15;
    voxel_space = gaussian_space_generate(l1, l2, l3, l4,...
                                          offset, box_size,...
                                          bump_center, bump_height, bump_width);
    cfg3.vol = voxel_space;
    cfg4 = cfg3;
    
    % Light source
    [x, y] = meshgrid(1:box_size, 1:box_size);
    bump = bump_height * exp(-((x-bump_center(1)).^2 + ...
            (y-bump_center(2)).^2)/(2*bump_width^2));
    bump = round(bump);

    cfg3.srcpos = [box_size/2, box_size/4, offset-1];
    cfg4.srcpos = [box_size/2, box_size * 3/4, offset-1];
    cfg3.srcpos(3) = cfg3.srcpos(3) + bump(cfg3.srcpos(1), cfg3.srcpos(2));
    cfg4.srcpos(3) = cfg4.srcpos(3) + bump(cfg4.srcpos(1), cfg4.srcpos(2));

    fluence3 = mcxlab(cfg3);
    fluence4 = mcxlab(cfg4);
    lgcwfluence3 = log(fluence3.data);
    lgcwfluence4 = log(fluence4.data);
    lgcwfluence = log(fluence3.data + fluence4.data);
    
    f4 = figure;
    f4.Position(1:2) = [1000, 300];
    f4.Position(3:4) = [800, 800];
    
    % mcxpreview(cfg2);
    % axis equal
    % 
    % imagesc(squeeze(lgcwfluence2(50, :, :)));
    % view(270, 90);
   
    % plot configs and results
    ax1 = subplot(221);
    mcxpreview(cfg3);
    ax1.Title.String = 'domain preview';
    axis equal
    
    ax2 = subplot(222);
    imagesc(squeeze(lgcwfluence(:, 50, :)));
    view(270, 90);
    ax2.XLim = [0, box_size];
    ax2.YLim = [0, box_size];
    ax2.CLim = [9, 18];
    ax2.DataAspectRatio = [1, 1, 1];
    ax2.Title.String = 'fluence at x=60';
    colorbar;
    hold on
    xline(offset+l1, 'w--');
    hold on
    xline(offset+l1+l2, 'w--');
    hold on
    xline(offset+l1+l2+l3, 'w--');
    hold off
    
    ax3 = subplot(223);
    target = max(lgcwfluence(:)) - 8;
    [xx1, yy1, zz1] = ind2sub(size(lgcwfluence), ...
                              find(lgcwfluence > target - 0.01 ...
                                 & lgcwfluence < target + 0.01));
    scatter3(xx1, yy1, zz1, 1, "filled", ...
             LineWidth=0.1);
    ax3.XLim = [0, box_size];
    ax3.YLim = [0, box_size];
    ax3.ZLim = [0, box_size];
    ax3.BoxStyle = "full";
    ax3.DataAspectRatio = [1, 1, 1];
    grid off
    
    ax4 = subplot(224);
    
    [row, col] = meshgrid(1:size(bump, 1), 1:size(bump, 2));
    indices = sub2ind(size(lgcwfluence), row, col, bump + offset + 6);
    slice = lgcwfluence(indices);
    imagesc(reshape(slice, size(bump)));
    ax4.XLim = [0, box_size];
    ax4.YLim = [0, box_size];
    ax4.CLim = [9, 18];
    ax4.DataAspectRatio = [1, 1, 1];
    ax4.Title.String = 'fluence at z=6';
    colorbar;
    
    figure;
    imagesc(squeeze(lgcwfluence(60, :, :)));
    view(270, 90);

    ax = gca;
    ax.XLim = [0, box_size];
    ax.YLim = [0, box_size];
    ax.CLim = [9, 18];
    ax.DataAspectRatio = [1, 1, 1];
    ax.Title.String = 'fluence at x=60';
    colorbar;
    hold on
    xline(offset+l1, 'w--');
    hold on
    xline(offset+l1+l2, 'w--');
    hold on
    xline(offset+l1+l2+l3, 'w--');
    hold off

    if rem(i, 50) ~= 0
        close all;
    end

    writematrix(slice, ...
            strcat('recording/slice_map/', ...
                   string(timestamps(i)), ...
                   '-y', ...
                   '.txt'));
    writematrix(squeeze(lgcwfluence(60, :, :)), ...
            strcat('recording/slice_map/', ...
                   string(timestamps(i)), ...
                   '-x', ...
                   '.txt'));
    fprintf(fid, '%d\t%d\t%d\t%d\t%d\t%d\n', [cfg3.srcpos, cfg4.srcpos]);

end

fclose(fid);
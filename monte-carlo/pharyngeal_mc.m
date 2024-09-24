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
cfg1.seed = 10086;
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
cfg1.srcparam1(1) = 10;        % variance in the zenith angle
cfg1.srcpos = [box_size/2, box_size/2, offset-1];
cfg1.srcdir = [0, 0, 1];

% Define light detector
cfg1.detpos = [cfg1.srcpos(1), cfg1.srcpos(2)-15, cfg1.srcpos(3)+2, 2];
cfg1.savedetflag = 'dspmxvw';

cfg1.tend = 5e-10;
fluence1 = mcxlab(cfg1);
lgcwfluence1 = log(fluence1.data);

f1 = figure;
f1.Position(1:2) = [1000, 300];
f1.Position(3:4) = [800, 800];

% plot configs and results
ax1 = subplot(221);
mcxpreview(cfg1);
ax1.Title.String = 'domain preview';
axis equal

ax2 = subplot(222);
imagesc(squeeze(lgcwfluence1(:, 50, :)));
view(270, 90);
ax2.XLim = [0, box_size];
ax2.YLim = [0, box_size];
ax2.CLim = [9, 18];
ax2.DataAspectRatio = [1, 1, 1];
ax2.Title.String = 'fluence at x=50';
colorbar;
hold on
xline(offset+l1, 'w--');
hold on
xline(offset+l1+l2, 'w--');
hold on
xline(offset+l1+l2+l3, 'w--');
hold off

ax3 = subplot(223);
thres = max(lgcwfluence1(:)) - 8;
[xx1, yy1, zz1] = ind2sub(size(lgcwfluence1), ...
                          find(lgcwfluence1 > thres - 0.01 ...
                             & lgcwfluence1 < thres + 0.01));
scatter3(xx1, yy1, zz1, 1, "filled", ...
         LineWidth=0.1);
ax3.XLim = [0, box_size];
ax3.YLim = [0, box_size];
ax3.ZLim = [0, box_size];
ax3.BoxStyle = "full";
ax3.DataAspectRatio = [1, 1, 1];
grid off

ax4 = subplot(224);
imagesc(squeeze(lgcwfluence1(:, :, cfg1.detpos(3))));
ax4.XLim = [0, box_size];
ax4.YLim = [0, box_size];
ax4.CLim = [9, 18];
ax4.DataAspectRatio = [1, 1, 1];
ax4.Title.String = 'fluence at z=6';
colorbar;

figure;
imagesc(squeeze(lgcwfluence1(50, :, :)));
view(270, 90);

ax = gca;
ax.XLim = [0, box_size];
ax.YLim = [0, box_size];
ax.CLim = [9, 18];
ax.DataAspectRatio = [1, 1, 1];
ax.Title.String = 'fluence at x=50';
colorbar;
hold on
xline(offset+l1, 'w--');
hold on
xline(offset+l1+l2, 'w--');
hold on
xline(offset+l1+l2+l3, 'w--');
hold off

% writematrix(squeeze(lgcwfluence1(50, :, :)), 'maps/flat.txt');

%% Bump translate

result = zeros(61, 10);

for ii = 1:60
    for jj = 1:10
        clearvars -except ...
            cfg1 result ...
            ii jj ...
            l1 l2 l3 l4 offset box_size
        cfg2 = cfg1;
        cfg2.tend = 5e-10;
    
        bump_center = [ii, 60];
        bump_height = -jj;
        bump_width = 15;
        voxel_space = gaussian_space_generate(l1, l2, l3, l4,...
                                          offset, box_size,...
                                          bump_center, bump_height, bump_width);
        cfg2.vol = voxel_space;
        cfg2.srcpos(3) = cfg2.srcpos(3)+bump_height;
        fluence2 = mcxlab(cfg2);
        lgcwfluence2 = log(fluence2.data);
        
        result(ii, jj) = lgcwfluence2(cfg2.detpos(1), ...
                                      cfg2.detpos(2), ...
                                      cfg2.detpos(3));
    end
end

%%
% writematrix(result, 'result/bump_loc_height_matrix.txt');

%% Example
cfg4 = cfg1;
cfg4.tend = 5e-10;

bump_center = [30, 60];
bump_height = -10;
bump_width = 15;
voxel_space = gaussian_space_generate(l1, l2, l3, l4,...
                                      offset, box_size,...
                                      bump_center, bump_height, bump_width);
cfg4.vol = voxel_space;
cfg4.srcpos(3) = cfg4.srcpos(3)+bump_height;

fluence4 = mcxlab(cfg4);
lgcwfluence4 = log(fluence4.data);

f4 = figure;
f4.Position(1:2) = [1000, 300];
f4.Position(3:4) = [800, 800];

% mcxpreview(cfg4);
% axis equal

imagesc(squeeze(lgcwfluence4(50, :, :)));
view(270, 90);

% plot configs and results
ax1 = subplot(221);
mcxpreview(cfg4);
ax1.Title.String = 'domain preview';
axis equal

ax2 = subplot(222);
imagesc(squeeze(lgcwfluence4(:, 50, :)));
view(270, 90);
ax2.XLim = [0, box_size];
ax2.YLim = [0, box_size];
ax2.CLim = [9, 18];
ax2.DataAspectRatio = [1, 1, 1];
ax2.Title.String = 'fluence at x=50';
colorbar;
hold on
xline(offset+l1, 'w--');
hold on
xline(offset+l1+l2, 'w--');
hold on
xline(offset+l1+l2+l3, 'w--');
hold off

ax3 = subplot(223);
thres = max(lgcwfluence4(:)) - 8;
[xx1, yy1, zz1] = ind2sub(size(lgcwfluence4), ...
                          find(lgcwfluence4 > thres - 0.01 ...
                             & lgcwfluence4 < thres + 0.01));
scatter3(xx1, yy1, zz1, 1, "filled", ...
         LineWidth=0.1);
ax3.XLim = [0, box_size];
ax3.YLim = [0, box_size];
ax3.ZLim = [0, box_size];
ax3.BoxStyle = "full";
ax3.DataAspectRatio = [1, 1, 1];
grid off

ax4 = subplot(224);
imagesc(squeeze(lgcwfluence4(:, :, cfg4.detpos(3))));
ax4.XLim = [0, box_size];
ax4.YLim = [0, box_size];
ax4.CLim = [9, 18];
ax4.DataAspectRatio = [1, 1, 1];
ax4.Title.String = 'fluence at z=6';
colorbar;

figure;
imagesc(squeeze(lgcwfluence4(50, :, :)));
view(270, 90);

ax = gca;
ax.XLim = [0, box_size];
ax.YLim = [0, box_size];
ax.CLim = [9, 18];
ax.DataAspectRatio = [1, 1, 1];
ax.Title.String = 'fluence at x=50';
colorbar;
hold on
xline(offset+l1, 'w--');
hold on
xline(offset+l1+l2, 'w--');
hold on
xline(offset+l1+l2+l3, 'w--');
hold off

thres1 = 11.5;
[xx1, yy1, zz1] = ind2sub(size(lgcwfluence4), ...
                          find(lgcwfluence4 > thres1 - 0.01 ...
                             & lgcwfluence4 < thres1 + 0.01));

thres2 = 10.5;
[xx2, yy2, zz2] = ind2sub(size(lgcwfluence4), ...
                          find(lgcwfluence4 > thres2 - 0.01 ...
                             & lgcwfluence4 < thres2 + 0.01));

% writematrix(squeeze(lgcwfluence4(50, :, :)), ...
%             strcat('maps/', ...
%                    string(bump_center(1)), ...
%                    '-', ...
%                    string(-bump_height), ...
%                    '.txt'));
% writematrix([xx1, yy1, zz1], ...
%             strcat('damping_scatter/', ...
%                    string(bump_center(1)), ...
%                    '-', ...
%                    string(-bump_height), ...
%                    '-1000.txt'));
% writematrix([xx2, yy2, zz2], ...
%             strcat('damping_scatter/', ...
%                    string(bump_center(1)), ...
%                    '-', ...
%                    string(-bump_height), ...
%                    '-10000.txt'));

%% Wait

exported_vol = cfg4.vol;
save example_bumped_voxel_space.mat exported_vol

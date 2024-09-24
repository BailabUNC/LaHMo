clc
clear
addpath('C:\Program Files (x86)\mcx-win-x86_64-v2020\mcx\utils\');
addpath('C:\Program Files (x86)\mcx-win-x86_64-v2020\mcxlab\');
addpath('C:\Program Files (x86)\mcx-win-x86_64-v2020\iso2mesh\');
% info = mcxlab('gpuinfo'); 

% define the simulation using a struct
cfg.nphoton = 1e7;                  % total number of photons
cfg.vol = uint8(ones(60, 60, 60));  % media index (start from 0)
% index 0 is the background, a photon terminates when moving
% from a non-zero to zero voxel

cfg.vol(20:40, 20:40, 10:30) = 2;   % add an inclusion
cfg.prop = [0,     0,   1,    1;
            0.005, 1,   0,    1.37;
            0.2,   10,  0.9,  1.37]; % [mua, mus, g, n]
cfg.issrcfrom0 = 1;
cfg.srctype = 'gaussian';
cfg.srcparam1 = 5;
cfg.srcpos = [30, 30, 1];
cfg.srcdir = [0, 0, 1];
cfg.detpos = [30, 20, 1, 1;
              30, 40, 1, 1;
              20, 30, 1, 1;
              40, 30, 1, 1];
cfg.vol(:, :, 1) = 0; % pad a layer of 0s to get diffuse reflectance
cfg.issaveref = 1;
cfg.gpuid = 1;
cfg.autopilot = 1;
cfg.tstart = 0;
cfg.tend = 5e-9;
cfg.tstep = 5e-10;

% calculate the fluence distribution with the given config
[fluence, detpt, vol, seeds, traj] = mcxlab(cfg);

% integrate time-axis (4th dimension) to get CW solutions
cwfluence = sum(fluence.data, 4); % fluence rate
cwdref = sum(fluence.dref, 4);    % diffuse reflectance

% plot configuration and results
subplot(231);
mcxpreview(cfg);
title('domain preview');

subplot(232);
imagesc(squeeze(log(cwfluence(:, 30, :))));
title('fluence at y=30');

subplot(233);
histogram(detpt.ppath(:, 1), 50);
title('partial path tissue #1');

subplot(234);
plot(squeeze(fluence.data(30, 30, 30, :)), '-o');
title('TPSF at [30, 30, 30]');

subplot(235);
newtraj = mcxplotphotons(traj);
title('photon trajectories');

subplot(236);
imagesc(squeeze(log(cwdref(:, :, 1))));
title('diffuse refle. at z=1')




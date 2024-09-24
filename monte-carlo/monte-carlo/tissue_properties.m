% skin parameters: doi:10.1142/S1793545811001319
% bone parameters: https://doi.org/10.1002/cnm.2826

clear
TISSUE_PROPERTIES_MAT = 1; % load flag

tprop.wavelength = 900; % nm

% epidermis
tprop.mus_epi = 33.6;   % cm-1 ref 57
tprop.mua_epi = 0.80;   % cm-1 ref 57
tprop.g_epi   = 0.89;
tprop.n_epi   = 1.31;   % eqn(30)

% dermis
tprop.mus_der = 20.1;   % cm-1 ref 57
tprop.mua_der = 0.83;   % cm-1 ref 57
tprop.g_der   = 0.89;
tprop.n_der   = 1.31;   % eqn(30)

% adipose
tprop.mus_adi = 18.5;   % cm-1 ref 57
tprop.mua_adi = 0.95;   % cm-1 ref 57
tprop.g_adi   = 0.89;
tprop.n_adi   = 1.44;   % ref 55

% muscle
tprop.mus_mus = 6.21;   % cm-1 ref 58
tprop.mua_mus = 0.32;   % cm-1 ref 58
tprop.g_mus   = 0.89;
tprop.n_mus   = 1.37;   % ref 55

% cartilage
tprop.mus_car = 148;    % cm-1
tprop.mua_car = 0.25;   % cm-1
tprop.g_car   = 0.9;
tprop.n_car   = 1.4;

% convert cm-1 to voxel-1
cm2voxel = 50;
tprop.mus_epi = tprop.mus_epi / cm2voxel;
tprop.mus_der = tprop.mus_der / cm2voxel;
tprop.mus_adi = tprop.mus_adi / cm2voxel;
tprop.mus_mus = tprop.mus_mus / cm2voxel;
tprop.mus_car = tprop.mus_car / cm2voxel;

tprop.mua_epi = tprop.mua_epi / cm2voxel;
tprop.mua_der = tprop.mua_der / cm2voxel;
tprop.mua_adi = tprop.mua_adi / cm2voxel;
tprop.mua_mus = tprop.mua_mus / cm2voxel;
tprop.mua_car = tprop.mua_car / cm2voxel;

save("tissue_properties.mat", "tprop", "TISSUE_PROPERTIES_MAT", "-mat");
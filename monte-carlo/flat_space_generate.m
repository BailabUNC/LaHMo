function voxel_space = flat_space_generate(l1, l2, l3, l4, offset, size)
%FLAT_SPACE_GENERATE Generate a 3D array that represents the geometry of 
% the tissue
%   Input: epidermis_thickness, dermis_thickness, fat_thickness,
%   muscle_thickness, offset, size
%   Output: voxel_space

voxel_space = zeros(size, size, size);

tissue_size = l1 + l2 + l3 + l4;
if tissue_size + offset * 2 > size
    error('Total thickness is too large.');
end

% Set tissue layers with different thickness
voxel_space(:, :, offset+1:offset+l1) = 1;
voxel_space(:, :, offset+l1+1:offset+l1+l2) = 2;
voxel_space(:, :, offset+l1+l2+1:offset+l1+l2+l3) = 3;
voxel_space(:, :, offset+l1+l2+l3+1:offset+l1+l2+l3+l4) = 4;
end


function voxel_space = gaussian_space_generate(l1, l2, l3, l4,...
                                               offset, size,...
                                               bump_center,...
                                               bump_height,...
                                               bump_width)
%GAUSSIAN_SPACE_GENERATE Generate a 3D array that represents the geometry 
% of the tissue
%   Input: l1, l2, l3, l4, offset, bump_center, bump_height, bump_width
%   Output: voxel_space

voxel_space = zeros(size, size, size);
tissue_size = l1 + l2 + l3 + l4;
if tissue_size + offset * 2 > size
    error('Total thickness is too large.');
end

% Create a 2D grid for x and y positions
[x, y] = meshgrid(1:size, 1:size);

% Calculate Gaussian bump
bump = bump_height * exp(-((x-bump_center(1)).^2 + (y-bump_center(2)).^2)/(2*bump_width^2));
bump = round(bump);

% Add tissue layers to voxel space
for i = 1:size
    for j = 1:size
        % epidermis
        voxel_space(i, j, ...
            (offset+bump(i, j)+1):(offset+bump(i, j)+l1)) = 1;
        % dermis
        voxel_space(i, j, ...
            (offset+bump(i, j)+l1+1):(offset+bump(i, j)+l1+l2)) = 2;
        % adipose
        voxel_space(i, j, ...
            (offset+bump(i, j)+l1+l2+1):(offset+bump(i, j)+l1+l2+l3)) = 3;
        % muscle
        voxel_space(i, j, ...
            (offset+bump(i, j)+l1+l2+l3+1):(offset+bump(i, j)+l1+l2+l3+l4)) = 4;
    end
end

end


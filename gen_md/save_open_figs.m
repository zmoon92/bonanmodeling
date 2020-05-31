function save_open_figs(dir)
% dir - the directory in which to save the figs
%
% requires 
% - export_fig <https://github.com/altmany/export_fig>
% 
% could do this with matlab.engine instead but for now this is easier

% get open figures
% https://stackoverflow.com/a/4540637
figHandles = findobj('Type', 'figure');

% loop through and save
for i = 1:size(figHandles, 1)

  h = figHandles(i);

  base_savename = sprintf('fig%02d', i);

  % form save path
  base_savepath = [dir, '/', base_savename];

  % save
  export_fig(h, base_savepath, '-transparent', '-png')

end


% OPTIONAL helper (requires GNU Octave): read a Qucs dataset and plot traces.
%
%   octave --quiet --eval "addpath('tools'); plot_waveforms('CMOS_NAND.dat.ngspice')"
%
% The Python verification suite needs no Octave; this script is only for
% interactive waveform inspection. It returns a struct with fields time,
% names and values, so you can also use it from Octave code:
%
%   d = plot_waveforms('CMOS_OR.dat.ngspice', false);
%   disp(d.names)
%
% With a third argument the plot is written to a PNG instead of displayed.

function data = plot_waveforms(filename, show_plot, output_file)
  if nargin < 1 || isempty(filename)
    filename = 'CMOS_NAND.dat.ngspice';
  end
  if nargin < 2
    show_plot = true;
  end
  if nargin < 3
    output_file = '';
  end

  text = fileread(filename);

  independent = regexp(text, '<indep\s+(\S+)\s+(\d+)>([^<]*)</indep>', 'tokens');
  if isempty(independent)
    error('No <indep> section found in %s', filename);
  end
  data.time = str2double(regexp(independent{1}{3}, '\S+', 'match'));

  dependencies = regexp(text, '<dep\s+(\S+)\s+\S+>([^<]*)</dep>', 'tokens');
  data.names = {};
  data.values = {};
  for k = 1:numel(dependencies)
    raw_name = dependencies{k}{1};
    node = regexp(raw_name, '\(([^)]+)\)', 'tokens');
    if isempty(node)
      short_name = raw_name;
    else
      short_name = node{1}{1};
    end
    values = str2double(regexp(dependencies{k}{2}, '\S+', 'match'));
    if numel(values) ~= numel(data.time)
      error('Signal %s has %d samples, expected %d', ...
            raw_name, numel(values), numel(data.time));
    end
    data.names{end+1} = lower(short_name);
    data.values{end+1} = values;
  end

  if isempty(data.names)
    error('No <dep> signals found in %s', filename);
  end

  if show_plot || ~isempty(output_file)
    figure('visible', 'off');
    for k = 1:numel(data.names)
      subplot(numel(data.names), 1, k);
      plot(data.time * 1e3, data.values{k}, 'linewidth', 1.2);
      grid on;
      ylabel(data.names{k});
      xlabel('time (ms)');
    end
    title(filename, 'interpreter', 'none');
    if ~isempty(output_file)
      print('-dpng', output_file);
    else
      figure(gcf);  % make the figure visible in an interactive session
    end
  end
end

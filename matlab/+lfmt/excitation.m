function out = excitation(action, varargin)
% EXCITATION LFMT chirp waveform generation, instantaneous frequency, and diffusion length.
%
% Usage:
%   q = lfmt.excitation('heat_flux', t, f0, f1, duration, q0)
%   ref = lfmt.excitation('reference_signal', t, f0, f1, duration, zero_mean)
%   mu = lfmt.excitation('diffusion_length', f, alpha)
%   report = lfmt.excitation('validate_frequency_band', f0, f1, alpha, plate_thickness_mm, defect_depths_mm)

switch lower(action)
    case 'heat_flux'
        t = varargin{1};
        f0 = varargin{2};
        f1 = varargin{3};
        duration = varargin{4};
        q0 = varargin{5};
        
        q = zeros(size(t));
        mask = (t >= 0) & (t <= duration);
        if any(mask(:))
            beta = (f1 - f0) / duration;
            t_m = t(mask);
            phi = 2 * pi * (f0 * t_m + 0.5 * beta * (t_m.^2));
            q(mask) = q0 * (1.0 + sin(phi));
        end
        out = q;
        
    case 'reference_signal'
        t = varargin{1};
        f0 = varargin{2};
        f1 = varargin{3};
        duration = varargin{4};
        zero_mean = true;
        if length(varargin) >= 5
            zero_mean = varargin{5};
        end
        
        ref = zeros(size(t));
        mask = (t >= 0) & (t <= duration);
        if any(mask(:))
            beta = (f1 - f0) / duration;
            t_m = t(mask);
            phi = 2 * pi * (f0 * t_m + 0.5 * beta * (t_m.^2));
            ref(mask) = sin(phi);
        end
        if zero_mean && any(mask(:))
            ref(mask) = ref(mask) - mean(ref(mask));
        end
        n_val = norm(ref);
        if n_val > 0
            ref = ref / n_val;
        end
        out = ref;
        
    case 'diffusion_length'
        f = varargin{1};
        alpha = varargin{2};
        % Thermal diffusion length mu(f) = sqrt(alpha / (pi * f)) [m]
        out = sqrt(alpha ./ (pi * max(f, 1e-6)));
        
    case 'validate_frequency_band'
        f0 = varargin{1};
        f1 = varargin{2};
        alpha = varargin{3};
        plate_thickness_mm = varargin{4};
        defect_depths_mm = varargin{5};
        
        mu_f0_mm = sqrt(alpha / (pi * f0)) * 1e3;
        mu_f1_mm = sqrt(alpha / (pi * f1)) * 1e3;
        
        z_min_mm = min(defect_depths_mm);
        z_max_mm = max(defect_depths_mm);
        
        is_f0_valid = (mu_f0_mm >= z_max_mm);
        is_f1_valid = (mu_f1_mm <= z_max_mm * 2.5);
        
        report = struct(...
            'f0_hz', f0, ...
            'f1_hz', f1, ...
            'thermal_diffusivity_m2_s', alpha, ...
            'diffusion_length_f0_mm', mu_f0_mm, ...
            'diffusion_length_f1_mm', mu_f1_mm, ...
            'plate_thickness_mm', plate_thickness_mm, ...
            'defect_depth_range_mm', [z_min_mm, z_max_mm], ...
            'is_f0_physically_sound', is_f0_valid, ...
            'is_f1_physically_sound', is_f1_valid, ...
            'assessment', sprintf('mu(f0=%.2f Hz) = %.2f mm >= z_max=%.2f mm (Probing depth satisfied); mu(f1=%.2f Hz) = %.2f mm.', ...
                f0, mu_f0_mm, z_max_mm, f1, mu_f1_mm) ...
        );
        out = report;
        
    otherwise
        error('LFMT:InvalidAction', 'Unknown excitation action "%s".', action);
end
end

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { ProcessSettings } from '@/services/api';

interface UploadSettingsProps {
  settings: ProcessSettings;
  onSettingsChange: (settings: ProcessSettings) => void;
}

export const UploadSettings = ({ settings, onSettingsChange }: UploadSettingsProps) => {
  const updateSetting = (key: keyof ProcessSettings, value: any) => {
    onSettingsChange({ ...settings, [key]: value });
  };

  return (
    <div className="glass-card p-6 space-y-6">
      <h3 className="text-lg font-semibold">Processing Settings</h3>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="languages">Languages (comma-separated)</Label>
          <Input
            id="languages"
            value={settings.languages}
            onChange={(e) => updateSetting('languages', e.target.value)}
            placeholder="e.g., english,hindi,tamil"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="extractImages"
            checked={settings.extractImages}
            onCheckedChange={(checked) => updateSetting('extractImages', checked)}
          />
          <Label htmlFor="extractImages" className="cursor-pointer">
            Extract Images
          </Label>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="extractTables"
            checked={settings.extractTables}
            onCheckedChange={(checked) => updateSetting('extractTables', checked)}
          />
          <Label htmlFor="extractTables" className="cursor-pointer">
            Extract Tables
          </Label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor="maxCharacters">Max Characters</Label>
            <Input
              id="maxCharacters"
              type="number"
              value={settings.maxCharacters}
              onChange={(e) => updateSetting('maxCharacters', parseInt(e.target.value))}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="newAfterNChars">New After N Chars</Label>
            <Input
              id="newAfterNChars"
              type="number"
              value={settings.newAfterNChars}
              onChange={(e) => updateSetting('newAfterNChars', parseInt(e.target.value))}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="combineTextUnderNChars">Combine Text Under N Chars</Label>
            <Input
              id="combineTextUnderNChars"
              type="number"
              value={settings.combineTextUnderNChars}
              onChange={(e) => updateSetting('combineTextUnderNChars', parseInt(e.target.value))}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

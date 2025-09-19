import React, { useEffect, useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import Input, { Textarea } from '../ui/Input';
import { showToast } from '../ui/Toast';
import { StrategyService } from '../../services/strategyService';
import type { Strategy } from '../../types';

interface StrategyEditorModalProps {
  isOpen: boolean;
  mode: 'edit' | 'create';
  strategy?: Strategy | null;
  onClose: () => void;
  onSaved?: () => void;
}

const toSnakeCase = (value: string): string =>
  value
    .replace(/[^a-zA-Z0-9]+/g, ' ')
    .trim()
    .replace(/\s+/g, '_')
    .toLowerCase();

const toPascalCase = (value: string): string =>
  toSnakeCase(value)
    .split('_')
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join('');

const ensurePythonExtension = (fileName: string): string =>
  fileName.endsWith('.py') ? fileName : `${fileName}.py`;

const buildTemplate = (classIdentifier: string): string => {
  const normalized = classIdentifier.endsWith('Strategy') ? classIdentifier : `${classIdentifier}Strategy`;
  return `"""Custom strategy created via in-app editor."""\n\nfrom backtester.strategy_base import StrategyBase\n\n\nclass ${normalized}(StrategyBase):\n    """Describe your strategy."""\n\n    NAME = "${normalized}"\n\n    def generate_signals(self, data):\n        """Return a pandas.Series with long/short/flat signals."""\n        # TODO: implement your entry logic\n        raise NotImplementedError("Implement your strategy logic")\n`; 
};

const StrategyEditorModal: React.FC<StrategyEditorModalProps> = ({
  isOpen,
  mode,
  strategy,
  onClose,
  onSaved
}) => {
  const [content, setContent] = useState('');
  const [fileName, setFileName] = useState('');
  const [filePath, setFilePath] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);

  const resetState = () => {
    setContent('');
    setFileName('');
    setFilePath('');
    setLoadError(null);
    setNameError(null);
    setIsLoading(false);
    setIsSaving(false);
  };

  useEffect(() => {
    if (!isOpen) {
      resetState();
      return;
    }

    if (mode === 'edit' && strategy) {
      setIsLoading(true);
      setLoadError(null);
      StrategyService.getStrategyCode(strategy.id)
        .then((source) => {
          setContent(source.content ?? '');
          setFilePath(source.file_path ?? '');
        })
        .catch((error) => {
          console.error('Failed to load strategy code:', error);
          setLoadError(error instanceof Error ? error.message : 'Failed to load strategy code');
          showToast.error('Failed to load strategy code');
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else if (mode === 'create') {
      const baseName = strategy?.name || 'New Strategy';
      const suggestedFileName = ensurePythonExtension(toSnakeCase(baseName) || 'custom_strategy');
      const className = toPascalCase(suggestedFileName.replace(/\.py$/i, '')) || 'Custom';

      setFileName(suggestedFileName);
      setContent(buildTemplate(className));
      setFilePath('');
      setLoadError(null);
      setNameError(null);
    }
  }, [isOpen, mode, strategy?.id]);

  const resolvedFilePath = useMemo(() => {
    if (mode === 'edit') {
      return filePath ? `strategies/${filePath}` : '';
    }
    const normalized = ensurePythonExtension(fileName.trim() || 'custom_strategy');
    return `strategies/${normalized}`;
  }, [filePath, fileName, mode]);

  const canSave = useMemo(() => {
    if (isLoading || isSaving) return false;
    if (!content.trim()) return false;
    if (mode === 'create' && !fileName.trim()) return false;
    if (mode === 'edit' && !strategy) return false;
    return true;
  }, [isLoading, isSaving, content, mode, fileName, strategy]);

  const handleSave = async () => {
    if (!content.trim()) {
      showToast.error('Strategy content cannot be empty');
      return;
    }

    if (mode === 'create') {
      const trimmed = fileName.trim();
      if (!trimmed) {
        setNameError('File name is required');
        return;
      }
      setNameError(null);
      setLoadError(null);
      setIsSaving(true);
      try {
        const normalized = ensurePythonExtension(trimmed);
        const result = await StrategyService.createStrategyFile({ file_name: normalized, content });

        if (result.registration?.success) {
          const registeredCount = result.registration.registered ?? result.registered_ids?.length ?? 0;
          const registeredDetail = registeredCount > 0 ? ` (${registeredCount} added)` : '';
          showToast.success(`Strategy created and registered${registeredDetail}`);
        } else if (result.registration) {
          const registrationErrors = result.registration.errors?.join('; ') || result.registration.error;
          showToast.success('Strategy file created');
          if (registrationErrors) {
            showToast.warning(`Registration issue: ${registrationErrors}`);
          } else {
            showToast.warning('Strategy saved but registration may require manual refresh');
          }
        } else {
          showToast.success('Strategy file created');
        }

        onSaved?.();
      } catch (error) {
        console.error('Failed to create strategy file:', error);
        const message = error instanceof Error ? error.message : 'Failed to create strategy file';
        setNameError(message.toLowerCase().includes('exists') ? 'A strategy with this file name already exists' : null);
        setLoadError(message.toLowerCase().includes('exists') ? null : message);
        showToast.error(message);
      } finally {
        setIsSaving(false);
      }
      return;
    }

    if (!strategy) {
      showToast.error('Strategy not found');
      return;
    }

    setIsSaving(true);
    setLoadError(null);
    try {
      const result = await StrategyService.updateStrategyCode(strategy.id, content);
      if (result.registration && !result.registration.success) {
        const registrationErrors = result.registration.errors?.join('; ') || result.registration.error;
        showToast.success('Strategy saved');
        if (registrationErrors) {
          showToast.warning(`Metadata refresh issue: ${registrationErrors}`);
        }
      } else {
        showToast.success('Strategy updated');
      }
      onSaved?.();
    } catch (error) {
      console.error('Failed to update strategy code:', error);
      const message = error instanceof Error ? error.message : 'Failed to update strategy code';
      setLoadError(message);
      showToast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'edit' ? `Edit ${strategy?.name || 'Strategy'}` : 'Create Strategy'}
      size="xl"
    >
      <div className="space-y-5">
        {mode === 'create' ? (
          <Input
            label="File name"
            value={fileName}
            onChange={(event) => setFileName(event.target.value)}
            placeholder="my_strategy.py"
            helpText="File will be saved inside the strategies/ directory"
            error={nameError || undefined}
          />
        ) : (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Editing file:
            <span className="ml-1 font-mono text-gray-900 dark:text-gray-100">{resolvedFilePath || 'Unknown path'}</span>
          </div>
        )}

        {loadError && (
          <div className="rounded-md border border-danger-200 bg-danger-50 px-3 py-2 text-sm text-danger-700 dark:border-danger-500/40 dark:bg-danger-900/30 dark:text-danger-300">
            {loadError}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-sm text-gray-500 dark:text-gray-400">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Loading strategy source...
          </div>
        ) : (
          <Textarea
            label="Strategy source"
            value={content}
            onChange={(event) => setContent(event.target.value)}
            rows={20}
            spellCheck={false}
            className="font-mono text-sm h-[420px]"
            resize="vertical"
            helpText="Use the editor to update the Python strategy implementation"
          />
        )}

        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {resolvedFilePath && <span>Stored at <span className="font-mono">{resolvedFilePath}</span></span>}
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" onClick={onClose} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!canSave} loading={isSaving}>
              {mode === 'edit' ? 'Save Changes' : 'Create Strategy'}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default StrategyEditorModal;

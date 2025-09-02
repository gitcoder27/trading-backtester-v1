import React from 'react';
import { Modal, Button, showToast } from '../../../components/ui';

interface DemoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const DemoModal: React.FC<DemoModalProps> = ({ isOpen, onClose }) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Demo Modal"
      size="md"
    >
      <div className="space-y-4">
        <p className="text-gray-600 dark:text-gray-400">
          This is a demo modal showcasing our design system. It supports:
        </p>
        
        <ul className="list-disc list-inside space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <li>Dark/light theme support</li>
          <li>Keyboard navigation (ESC to close)</li>
          <li>Click outside to close</li>
          <li>Accessible ARIA attributes</li>
          <li>Smooth animations</li>
        </ul>

        <div className="flex space-x-3 pt-4">
          <Button 
            variant="primary" 
            onClick={() => {
              showToast.success('Success!', 'This is a success toast message.');
              onClose();
            }}
          >
            Show Success Toast
          </Button>
          <Button 
            variant="outline" 
            onClick={() => {
              showToast.warning('Warning!', 'This is a warning toast message.');
            }}
          >
            Show Warning
          </Button>
          <Button 
            variant="ghost" 
            onClick={onClose}
          >
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default DemoModal;

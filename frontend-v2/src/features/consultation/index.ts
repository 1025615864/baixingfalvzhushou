// Consultation Feature Module
export { ConsultationList } from './components/ConsultationList';
export { ConsultationDetail } from './components/ConsultationDetail';
export { ConsultationCard } from './components/ConsultationCard';
export { CreateConsultationModal } from './components/CreateConsultationModal';

export { useConsultations } from './hooks/useConsultations';
export { useConsultationDetail } from './hooks/useConsultationDetail';
export { useCreateConsultation } from './hooks/useCreateConsultation';

export type {
  Consultation,
  ConsultationStatus,
  ConsultationCategory,
  ConsultationTemplate,
  ConsultationQuestion,
  CreateConsultationRequest,
} from './types';
// frontend/src/components/common/Dialog.tsx
import React from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import { cn } from '../../utils/cn'

export interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
  className?: string
}

export const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children, className }) => {
  if (!open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
    >
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      <div className={cn('relative z-50 w-full max-w-lg mx-4', className)}>
        {children}
      </div>
    </div>,
    document.body
  )
}

export interface DialogContentProps {
  children: React.ReactNode
  className?: string
  showCloseButton?: boolean
  onClose?: () => void
}

export const DialogContent: React.FC<DialogContentProps> = ({
  children,
  className,
  showCloseButton = true,
  onClose
}) => {
  return (
    <div
      className={cn(
        'bg-background border border-border rounded-xl shadow-2xl overflow-hidden',
        className
      )}
    >
      {showCloseButton && (
        <button
          onClick={onClose}
          className="absolute transition-opacity rounded-sm right-4 top-4 opacity-70 ring-offset-background hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          <X className="w-4 h-4" />
          <span className="sr-only">Close</span>
        </button>
      )}
      {children}
    </div>
  )
}

export interface DialogHeaderProps {
  children: React.ReactNode
  className?: string
}

export const DialogHeader: React.FC<DialogHeaderProps> = ({ children, className }) => {
  return (
    <div className={cn('flex flex-col space-y-1.5 text-center sm:text-left p-6 pb-3', className)}>
      {children}
    </div>
  )
}

export interface DialogTitleProps {
  children: React.ReactNode
  className?: string
}

export const DialogTitle: React.FC<DialogTitleProps> = ({ children, className }) => {
  return (
    <h2 className={cn('text-lg font-semibold leading-none tracking-tight', className)}>
      {children}
    </h2>
  )
}

export interface DialogDescriptionProps {
  children: React.ReactNode
  className?: string
}

export const DialogDescription: React.FC<DialogDescriptionProps> = ({ children, className }) => {
  return (
    <p className={cn('text-sm text-muted-foreground', className)}>
      {children}
    </p>
  )
}

export interface DialogFooterProps {
  children: React.ReactNode
  className?: string
}

export const DialogFooter: React.FC<DialogFooterProps> = ({ children, className }) => {
  return (
    <div className={cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 p-6 pt-3', className)}>
      {children}
    </div>
  )
}

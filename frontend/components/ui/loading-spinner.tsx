import { cn } from "@/lib/utils"

interface LoadingSpinnerProps extends React.HTMLAttributes<HTMLDivElement> {}

export function LoadingSpinner({ className, ...props }: LoadingSpinnerProps) {
  return (
    <div 
      className={cn(
        "animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary",
        className
      )}
      {...props}
    />
  )
}

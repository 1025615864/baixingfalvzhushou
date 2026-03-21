export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
  className?: string;
}

export function Breadcrumb({
  items,
  separator = '/',
  className = '',
}: BreadcrumbProps) {
  return (
    <nav className={`flex items-center space-x-2 text-sm ${className}`}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <div key={index} className="flex items-center space-x-2">
            {index > 0 && (
              <span className="text-gray-400">{separator}</span>
            )}
            {isLast || !item.href ? (
              <span className={`flex items-center gap-1 ${isLast ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
                {item.icon}
                {item.label}
              </span>
            ) : (
              <a
                href={item.href}
                className="flex items-center gap-1 text-gray-500 hover:text-gray-900 transition-colors"
              >
                {item.icon}
                {item.label}
              </a>
            )}
          </div>
        );
      })}
    </nav>
  );
}

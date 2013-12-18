class CreateTwitters < ActiveRecord::Migration
  def change
    create_table :twitters do |t|
      t.string :handle
      t.text :tweet

      t.timestamps
    end
  end
end
